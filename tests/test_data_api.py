import json
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,select,func
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from services.data import parse_csv,validate_calls,normalized_calls
from services.database import metadata,train_calls,ingest_calls,read_calls
from services.queues import Config,run
from data_api import app as data_app
from api import app

SAMPLE=Path(__file__).parents[1]/'data/example_train_calls.csv'

def records():
    return parse_csv(SAMPLE.read_bytes())


def test_csv_and_observed_queue_counts():
    calls=records()
    out=run(Config(train_calls=normalized_calls(calls)))
    assert out['passengers']==2400
    assert out['attempts']==600
    assert out['station_visits']+out['unserved_attempts']==600

@pytest.mark.parametrize('change',[{'departure_at':'2026-10-23T08:00:00'},
                                 {'boarding_passengers':-1},
                                 {'attempts_urinal':10001},
                                 {'unexpected':'x'}])
def test_invalid_records_rejected(change):
    rows=[x.model_dump(mode='json') for x in records()]
    rows[0].update(change)
    with pytest.raises(ValueError):
        validate_calls(rows)


def test_duplicates_and_mixed_platforms_rejected():
    rows=[x.model_dump() for x in records()]
    with pytest.raises(ValueError):validate_calls(rows+[rows[0]])
    rows[0]['platform']='2'
    with pytest.raises(ValueError):validate_calls(rows)


def test_database_roundtrip_and_atomic_duplicates():
    db=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    metadata.create_all(db)
    assert ingest_calls(records(),db)==3
    assert len(read_calls('DEMO','1','2026-10-23',db))==3
    assert read_calls("' OR 1=1--",'1','2026-10-23',db)==[]
    with pytest.raises(IntegrityError):ingest_calls(records(),db)
    with db.connect() as c:
        assert c.scalar(select(func.count()).select_from(train_calls))==3


def test_data_api_requires_authentication(monkeypatch):
    monkeypatch.setenv('DATA_API_TOKEN','t'*32)
    c=TestClient(data_app)
    params={'station':'DEMO','platform':'1','service_date':'2026-10-23'}
    assert c.get('/v1/data/train-calls',params=params).status_code==401
    with patch('data_api.read_calls',return_value=records()):
        r=c.get('/v1/data/train-calls',params=params,headers={'Authorization':'Bearer '+'t'*32})
    assert r.status_code==200 and len(r.json()['records'])==3


def test_data_api_fails_closed_without_token(monkeypatch):
    monkeypatch.delenv('DATA_API_TOKEN',raising=False)
    c=TestClient(data_app)
    assert c.get('/v1/data/train-calls',params={'station':'DEMO','platform':'1','service_date':'2026-10-23'}).status_code==503


def test_queue_api_validated_and_observed():
    c=TestClient(app)
    assert c.post('/v1/queues/compare',json={'counts':[-1,2,3,4]}).status_code==422
    assert c.post('/v1/queues/compare',json={'repeats':1000}).status_code==422
    r=c.post('/v1/queues/compare',json={'passengers':100,'repeats':5,'calls':[x.model_dump(mode='json') for x in records()]})
    assert r.status_code==200,r.text
    assert len(r.json()['results'])==3
    assert c.get('/health').json()['version']=='6.0.0'
