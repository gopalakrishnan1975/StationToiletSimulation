from services.infrastructure import Inputs,calculate
from services.welfare import Policy,evaluate
from services.optimization import optimize

def test_free_fee_zero():
    r=evaluate(Policy(),Inputs())
    assert r['gross_fees_lakh_year']==0
    assert r['discouraged_wc_day']==0
    assert r['incremental_social_vs_free_lakh_year']==0

def test_tariff_transfer_not_social_benefit():
    r=evaluate(Policy(tariff_wc=5),Inputs())
    assert r['gross_fees_lakh_year']>0
    assert r['incremental_social_vs_free_lakh_year']<0

def test_water_scales():
    a=calculate(Inputs(trains_day=10))
    b=calculate(Inputs(trains_day=20))
    assert b['water_kld']>a['water_kld']
    assert b['stp_kld']>=a['stp_kld']

def test_optimizer():
    r=optimize(Inputs())
    assert r['social_welfare_choice'] is not None
