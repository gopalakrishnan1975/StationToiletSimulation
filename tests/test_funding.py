from services.infrastructure import Inputs
from services.funding import Funding,evaluate
def test_unit_cost_and_budget_balance():
    r=evaluate(Funding(),Inputs())
    assert r['unit_cost_per_boarding_rs']>0
    assert r['surplus_gap_lakh']<0
def test_allocated_existing_fares_are_separate_from_incremental():
    r=evaluate(Funding(allocated_existing_fare_rs=3),Inputs())
    assert r['existing_fare_allocation_lakh']>0
    assert r['incremental_fare_revenue_lakh']==0
