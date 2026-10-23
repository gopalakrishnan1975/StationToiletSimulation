from dataclasses import dataclass
@dataclass
class Premium:
    paying_visits_day:int=150
    charge_rs:float=10
    variable_cost_rs:float=3
    extra_annual_maintenance_lakh:float=3
    annualized_capex_lakh:float=2
    collection_cost_lakh:float=1

def evaluate(x:Premium):
    revenue=x.paying_visits_day*x.charge_rs*365/100000
    resource=x.paying_visits_day*x.variable_cost_rs*365/100000+x.extra_annual_maintenance_lakh+x.annualized_capex_lakh+x.collection_cost_lakh
    return dict(revenue_lakh=round(revenue,2),resource_cost_lakh=round(resource,2),budget_surplus_lakh=round(revenue-resource,2),note='Premium facility must be additional; free basic toilets cannot be displaced.')
