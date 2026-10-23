"""Separately deployable, authenticated read API over aggregate train-call records."""
import os
import secrets
from datetime import date
from fastapi import FastAPI,Depends,Header,HTTPException,Query
from sqlalchemy.exc import SQLAlchemyError
from services.database import read_calls

app=FastAPI(title='Station Sanitation Data API',version='6.0.0')


def require_token(authorization: str|None=Header(default=None)):
    expected=os.environ.get('DATA_API_TOKEN')
    if not expected or len(expected)<32:
        raise HTTPException(503,'Data service authentication is not configured')
    if not authorization or not authorization.startswith('Bearer ') or not secrets.compare_digest(authorization[7:],expected):
        raise HTTPException(401,'Valid bearer token required',headers={'WWW-Authenticate':'Bearer'})

@app.get('/health')
def health():
    return {'status':'ok','version':'6.0.0','database_configured':bool(os.environ.get('DATABASE_URL'))}

@app.get('/v1/data/train-calls',dependencies=[Depends(require_token)])
def get_calls(station: str=Query(pattern=r'^[A-Z0-9]{1,12}$'),
              platform: str=Query(min_length=1,max_length=12,pattern=r'^[A-Za-z0-9 -]+$'),
              service_date: date=Query()):
    try:
        calls=read_calls(station,platform,service_date)
    except (SQLAlchemyError,RuntimeError):
        raise HTTPException(503,'Aggregate data source is unavailable') from None
    except ValueError:
        raise HTTPException(422,'Stored records fail the aggregate data contract') from None
    return {'schema_version':'1.0','source':'configured station aggregate database',
            'records':[c.model_dump(mode='json') for c in calls]}
