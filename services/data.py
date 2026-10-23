"""Validated aggregate train-call data contract shared by CSV, API and database."""
import csv
import io
import json
import hashlib
from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

KINDS=('urinal','male_wc','female_wc','accessible_wc')

class TrainCall(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    station_code: str=Field(min_length=1,max_length=12,pattern=r'^[A-Z0-9]+$')
    platform: str=Field(min_length=1,max_length=12,pattern=r'^[A-Za-z0-9 -]+$')
    train_id: str=Field(min_length=1,max_length=20,pattern=r'^[A-Za-z0-9_-]+$')
    departure_at: datetime
    boarding_passengers: int=Field(ge=1,le=10000)
    attempts_urinal: int|None=Field(default=None,ge=0,le=10000)
    attempts_male_wc: int|None=Field(default=None,ge=0,le=10000)
    attempts_female_wc: int|None=Field(default=None,ge=0,le=10000)
    attempts_accessible_wc: int|None=Field(default=None,ge=0,le=10000)

    @field_validator('departure_at')
    @classmethod
    def timezone_required(cls,v):
        if v.tzinfo is None or v.utcoffset() != timedelta(hours=5,minutes=30):
            raise ValueError('departure_at must include the +05:30 Indian time offset')
        return v

    @model_validator(mode='after')
    def attempts_consistent(self):
        vals=[getattr(self,'attempts_'+k) for k in KINDS]
        if any(v is not None for v in vals):
            if any(v is None for v in vals):
                raise ValueError('Provide all four attempt counts, or leave all blank')
            if sum(vals)>self.boarding_passengers:
                raise ValueError('Attempts cannot exceed boardings in this one-use-per-passenger model')
        return self


def validate_calls(rows):
    if not rows or len(rows)>100:
        raise ValueError('Provide 1–100 train calls for one station, platform and date')
    calls=[TrainCall.model_validate(r) for r in rows]
    if len({(c.station_code,c.platform,c.departure_at.date()) for c in calls})!=1:
        raise ValueError('Select one station, platform and Indian service date per simulation')
    keys=[(c.train_id,c.departure_at) for c in calls]
    if len(keys)!=len(set(keys)):
        raise ValueError('Duplicate train call: train_id and departure_at must be unique')
    if sum(c.boarding_passengers for c in calls)>50000:
        raise ValueError('Maximum 50,000 boarding passengers per data batch')
    observed=[c.attempts_urinal is not None for c in calls]
    if any(observed) and not all(observed):
        raise ValueError('Do not mix observed-attempt and assumed-demand rows')
    return sorted(calls,key=lambda c:c.departure_at)


def parse_csv(content):
    if len(content)>1_000_000:
        raise ValueError('CSV must be no larger than 1 MB')
    reader=csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
    rows=[{k:v for k,v in row.items() if v not in ('',None)} for row in reader]
    return validate_calls(rows)


def normalized_calls(calls):
    calls=validate_calls([c.model_dump() if isinstance(c,TrainCall) else c for c in calls])
    first=calls[0].departure_at
    return tuple({'departure_min':(c.departure_at-first).total_seconds()/60,
                  'passengers':c.boarding_passengers,
                  'attempts': {k:getattr(c,'attempts_'+k) for k in KINDS} if c.attempts_urinal is not None else None}
                 for c in calls)


def provenance(calls,source):
    rows=[c.model_dump(mode='json') for c in calls]
    return {'source':source,'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),
            'rows':len(rows),'station':calls[0].station_code,'platform':calls[0].platform,
            'service_date':str(calls[0].departure_at.date()),'boardings':sum(c.boarding_passengers for c in calls),
            'demand_basis':'observed attempts' if calls[0].attempts_urinal is not None else 'assumed use probability',
            'note':'Arrival times within each window, spatial origins and service durations remain synthetic.'}
