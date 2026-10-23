from dataclasses import dataclass, asdict
from math import isfinite
from .infrastructure import Inputs, calculate

@dataclass
class Funding:
    annual_boardings:int=7_300_000
    annual_non_boarding_visits:int=0
    nonfare_revenue_lakh:float=0.0
    allocated_existing_fare_rs:float=0.0
    proposed_incremental_fare_rs:float=0.0
    allocation_by_passenger_km:bool=False
    annual_passenger_km:float=0.0
    proposed_rate_per_pkm_rs:float=0.0
    low_income_share:float=0.4
    low_income_surcharge_exempt:bool=False
    revenue_leakage_fraction:float=0.0
    fare_demand_elasticity:float=0.0
    average_base_fare_rs:float=100.0
    station_support_grant_lakh:float=0.0
    discount:float=.08
    asset_life_years:int=15
    # Distribution of existing fare allocation is a budgeting transfer, not necessarily a fare increase.

def evaluate(f:Funding, x:Inputs):
    c=calculate(x)
    ann=f.discount/(1-(1+f.discount)**(-f.asset_life_years)) if f.discount>0 else 1/f.asset_life_years
    cap_ann=c['capex_lakh']*ann
    full=c['opex_lakh_year']+cap_ann
    fee_inc=f.proposed_incremental_fare_rs
    paying_fraction=1-f.low_income_share if f.low_income_surcharge_exempt else 1
    demand_multiplier=max(0.0,1+f.fare_demand_elasticity*fee_inc/max(1,f.average_base_fare_rs))
    billable=f.annual_boardings*demand_multiplier*paying_fraction
    existing=f.annual_boardings*f.allocated_existing_fare_rs/100000
    incremental=billable*fee_inc/100000
    pkm=f.annual_passenger_km*f.proposed_rate_per_pkm_rs/100000 if f.allocation_by_passenger_km else 0
    available=(existing+incremental+pkm)*(1-f.revenue_leakage_fraction)+f.nonfare_revenue_lakh+f.station_support_grant_lakh
    # Passenger surcharge is a transfer, not gross social gain; avoids double counting.
    return {'annual_boardings':round(f.annual_boardings*demand_multiplier),'annualized_capex_lakh':round(cap_ann,2),
            'annual_opex_lakh':round(c['opex_lakh_year'],2),'annual_funding_need_lakh':round(full,2),
            'unit_cost_per_boarding_rs':round(full*100000/max(1,f.annual_boardings),2),
            'existing_fare_allocation_lakh':round(existing,2),'incremental_fare_revenue_lakh':round(incremental,2),
            'pkm_allocation_lakh':round(pkm,2),'all_funding_lakh':round(available,2),
            'surplus_gap_lakh':round(available-full,2),
            'required_allocation_per_boarding_rs':round(max(0,(full-f.nonfare_revenue_lakh-f.station_support_grant_lakh)/max(.000001,1-f.revenue_leakage_fraction)-incremental-pkm)*100000/max(1,f.annual_boardings),2),
            'break_even_boardings_at_allocated_rs':round(max(0,full-f.nonfare_revenue_lakh-f.station_support_grant_lakh-pkm*(1-f.revenue_leakage_fraction))*100000/((f.allocated_existing_fare_rs+fee_inc*demand_multiplier*paying_fraction)*(1-f.revenue_leakage_fraction))) if (f.allocated_existing_fare_rs+fee_inc*demand_multiplier*paying_fraction)*(1-f.revenue_leakage_fraction)>0 else None,
            'formula_note':'Charges or allocated fare receipts are financing transfers; welfare must separately include accessibility, diversion, operating resources, quality, distributional weights, and demand loss.'}
