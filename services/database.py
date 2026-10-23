"""Aggregate-data adapter. No credentials or database objects are exposed to clients."""
import json
import os
from contextlib import contextmanager
from functools import lru_cache
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Text, select
from .data import TrainCall,validate_calls

metadata=MetaData()
train_calls=Table('sanitation_train_calls',metadata,
    Column('station_code',String(12),primary_key=True),
    Column('platform',String(12),primary_key=True),
    Column('train_id',String(20),primary_key=True),
    Column('departure_at',String(40),primary_key=True),
    Column('service_date',String(10),nullable=False,index=True),
    Column('boarding_passengers',Integer,nullable=False),
    Column('payload',Text,nullable=False))

@lru_cache(maxsize=1)
def engine():
    url=os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError('Database is not configured')
    return create_engine(url,pool_pre_ping=True)


def read_calls(station,platform,service_date,db=None):
    db=db or engine()
    query=select(train_calls.c.payload).where(
        train_calls.c.station_code==station,
        train_calls.c.platform==platform,
        train_calls.c.service_date==str(service_date)).limit(101)
    with db.connect() as connection:
        rows=connection.execute(query).scalars().all()
    return validate_calls([json.loads(x) for x in rows]) if rows else []


def ingest_calls(calls,db=None):
    """Offline trusted import only. Existing keys are rejected; writes are atomic."""
    db=db or engine()
    calls=validate_calls([c.model_dump() if isinstance(c,TrainCall) else c for c in calls])
    rows=[dict(station_code=c.station_code,platform=c.platform,train_id=c.train_id,
               departure_at=c.departure_at.isoformat(),service_date=str(c.departure_at.date()),
               boarding_passengers=c.boarding_passengers,payload=c.model_dump_json()) for c in calls]
    with db.begin() as connection:
        connection.execute(train_calls.insert(),rows)
    return len(rows)
