from fastapi import FastAPI
from pydantic import BaseModel,Field
from services.infrastructure import Inputs,calculate
from services.funding import Funding,evaluate as funding_evaluate
from services.welfare import Policy,evaluate,compare
from services.roster import staffing
from services.optimization import optimize
from services.queues_v3 import run_36_fixture_layout

app=FastAPI(title='Station Sanitation Microservice Gateway',version='4.0')
class InfrastructureRequest(BaseModel):
    trains_day:int=Field(20,ge=1,le=500)
    passengers_train:int=Field(1000,ge=1,le=10000)
    station_use:float=Field(.25,ge=0,le=1)
    urinal_share:float=Field(.375,ge=0,le=1)
class WelfareRequest(BaseModel):
    tariff_wc:float=Field(0,ge=0,le=100)
    demand_response:float=Field(-.25,ge=-3,le=0)
    onboard_diversion:float=Field(.30,ge=0,le=1)
    value_of_visit_rs:float=Field(12,ge=0)
    infra:InfrastructureRequest=InfrastructureRequest()
def as_infra(i):return Inputs(**i.model_dump())
@app.get('/health')
def health():return {'status':'ok','version':'5.0'}
@app.post('/v1/infrastructure/size')
def size(i:InfrastructureRequest):return calculate(as_infra(i))
@app.post('/v1/welfare/evaluate')
def welfare(req:WelfareRequest):return evaluate(Policy(tariff_wc=req.tariff_wc,demand_response=req.demand_response,onboard_diversion=req.onboard_diversion,value_of_visit_rs=req.value_of_visit_rs),as_infra(req.infra))
@app.post('/v1/welfare/compare')
def welfare_compare(i:InfrastructureRequest):return compare(as_infra(i))
@app.post('/v1/operations/staff')
def staff():return staffing()
@app.post('/v1/optimization/policies')
def policy_opt(i:InfrastructureRequest):return optimize(as_infra(i))
@app.get('/v1/queues/example')
def queue_example():return run_36_fixture_layout()

class FundingRequest(BaseModel):
    annual_boardings:int=Field(7300000,ge=1)
    allocated_existing_fare_rs:float=Field(0,ge=0)
    proposed_incremental_fare_rs:float=Field(0,ge=0)
    nonfare_revenue_lakh:float=Field(0,ge=0)
    station_support_grant_lakh:float=Field(0,ge=0)
    infra:InfrastructureRequest=InfrastructureRequest()
@app.post('/v1/funding/fare-entitlement')
def fare_entitlement(req:FundingRequest):
    return funding_evaluate(Funding(annual_boardings=req.annual_boardings,allocated_existing_fare_rs=req.allocated_existing_fare_rs,proposed_incremental_fare_rs=req.proposed_incremental_fare_rs,nonfare_revenue_lakh=req.nonfare_revenue_lakh,station_support_grant_lakh=req.station_support_grant_lakh),as_infra(req.infra))
