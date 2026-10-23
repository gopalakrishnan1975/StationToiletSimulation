from dataclasses import dataclass,asdict
from math import pow
from .infrastructure import Inputs,calculate

@dataclass
class Policy:
    tariff_wc:float=0
    premium_tariff:float=0
    premium_share:float=0
    exempt_share:float=.10
    demand_response:float=-.25
    female_share:float=.50
    lower_income_share:float=.40
    equity_weight:float=1.5
    collection_fraction:float=.08
    collection_fixed_lakh:float=8
    onboard_diversion:float=.30
    onboard_damage_rs:float=15
    station_variable_rs:float=2
    value_of_visit_rs:float=12
    value_of_time_rs_hour:float=60
    queue_minutes_saved:float=0
    annual_health_benefit_lakh:float=0
    annual_environment_benefit_lakh:float=0
    annual_premium_service_cost_lakh:float=0
    social_discount_rate:float=.08
    years:int=15

def evaluate(policy:Policy, infra:Inputs):
    # Compare policies on a common free-access potential market, not endogenous realized use.
    base=infra.trains_day*infra.passengers_train*infra.station_use
    wc=base*(1-infra.urinal_share)
    urinal=base-wc
    multiplier=pow(1+policy.tariff_wc/5,policy.demand_response)
    realized_wc=wc*multiplier
    lost=max(0,wc-realized_wc)
    charged=realized_wc*(1-policy.exempt_share)
    gross_lakh=charged*policy.tariff_wc*365/100000
    premium_revenue_lakh=realized_wc*policy.premium_share*policy.premium_tariff*365/100000
    collection_lakh=(gross_lakh+premium_revenue_lakh)*policy.collection_fraction+(policy.collection_fixed_lakh if policy.tariff_wc>0 or policy.premium_tariff>0 else 0)
    lost_welfare_lakh=lost*policy.value_of_visit_rs*365/100000*(1+policy.lower_income_share*(policy.equity_weight-1))
    coach_cost_lakh=lost*policy.onboard_diversion*policy.onboard_damage_rs*365/100000
    saved_variable_lakh=lost*policy.station_variable_rs*365/100000
    # Charging receipts are transfers, excluded from social surplus; collection is real resource use.
    incremental_social_lakh= -lost_welfare_lakh-coach_cost_lakh+saved_variable_lakh-collection_lakh-policy.annual_premium_service_cost_lakh+policy.annual_health_benefit_lakh+policy.annual_environment_benefit_lakh
    incremental_financial_lakh=gross_lakh+premium_revenue_lakh-collection_lakh+saved_variable_lakh-policy.annual_premium_service_cost_lakh
    annual_cost=calculate(infra)['opex_lakh_year']
    return dict(policy=asdict(policy),potential_wc_day=round(wc),realized_wc_day=round(realized_wc),urinal_day=round(urinal),discouraged_wc_day=round(lost),gross_fees_lakh_year=round(gross_lakh+premium_revenue_lakh,2),collection_cost_lakh_year=round(collection_lakh,2),incremental_financial_vs_free_lakh_year=round(incremental_financial_lakh,2),incremental_social_vs_free_lakh_year=round(incremental_social_lakh,2),annual_opex_lakh=round(annual_cost,2),annual_capex_equivalent_lakh=round(calculate(infra)['capex_lakh']*(policy.social_discount_rate/(1-(1+policy.social_discount_rate)**(-policy.years))),2),distributional_warning='Equity-weighted access value is illustrative, not a validated willingness-to-pay estimate')

def compare(infra=None):
    x=infra or Inputs()
    return {k:evaluate(v,x) for k,v in {'free_basic':Policy(),'pay_wc_2':Policy(tariff_wc=2),'pay_wc_5':Policy(tariff_wc=5),'free_basic_premium':Policy(premium_tariff=10,premium_share=.10,annual_premium_service_cost_lakh=3)}.items()}
