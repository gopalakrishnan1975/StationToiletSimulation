from dataclasses import replace
import math
import pytest
from services.queues import Config,simulate,run
from services.welfare import Policy,evaluate,compare
from services.infrastructure import Inputs,calculate
from services.funding import Funding,evaluate as funding
from services.experiments import compare_layouts


def test_fcfs_uses_facility_arrival_not_platform_arrival():
    cfg=Config(stations=(0,),urinals=(1,),male_wc=(0,),female_wc=(0,),accessible_wc=(0,))
    out=simulate(cfg,[dict(arrival=0,position=600,departure=60,kind='urinal',duration=5,train=0),
                      dict(arrival=1,position=0,departure=60,kind='urinal',duration=1,train=0)])
    assert out[0]['arrival']==1 and out[0]['service_start']==1
    assert out[1]['arrival']==0 and out[1]['service_start']==10


def test_return_walk_and_service_must_fit():
    cfg=Config(stations=(0,),urinals=(1,),male_wc=(0,),female_wc=(0,),accessible_wc=(0,))
    out=simulate(cfg,[dict(arrival=0,position=120,departure=7,kind='urinal',duration=2,train=0)])
    assert out[0]['reason']=='boarding_deadline'  # 2+2+2 > 7-2


def test_single_fixture_never_overlaps():
    cfg=Config(stations=(0,),urinals=(1,),male_wc=(0,),female_wc=(0,),accessible_wc=(0,))
    out=simulate(cfg,[dict(arrival=i*.1,position=0,departure=100,kind='urinal',duration=1,train=0) for i in range(30)])
    intervals=sorted((x['service_start'],x['service_end']) for x in out if x['served'])
    assert all(b[0]>=a[1] for a,b in zip(intervals,intervals[1:]))


@pytest.mark.parametrize('changes',[{'walking_m_per_min':0},{'use_probability':math.nan},{'male_fraction':2},{'urinals':(.5,1,1)},{'headway_min':0}])
def test_invalid_queue_parameters(changes):
    with pytest.raises(ValueError):
        run(replace(Config(),**changes))


def test_zero_demand_does_not_report_service_success():
    rows=compare_layouts(100,0,600,30,30,2,5,(9,6,18,3),3)
    assert all(r['Overall service target']!='Met' for r in rows)


def test_queue_target_cannot_hide_unmet_demand():
    rows=compare_layouts(1000,1,600,5,5,2,5,(1,1,1,1),30)
    assert all(r['Overall service target']!='Met' for r in rows)


def test_price_exemptions_keep_demand():
    x=Inputs()
    a=evaluate(Policy(tariff_wc=10,exempt_share=1),x)
    assert a['discouraged_wc_day']==0 and a['gross_fees_lakh_year']==0


def test_comparisons_follow_current_behaviour():
    x=Inputs()
    a=compare(x,Policy(demand_response=0))
    assert a['pay_wc_5']['discouraged_wc_day']==0
    assert a['pay_wc_5']['realized_wc_day']==a['free_basic']['realized_wc_day']


def test_zero_discount_supported():
    assert evaluate(Policy(social_discount_rate=0),Inputs())['annual_capex_equivalent_lakh']>0


def test_water_mass_balance_and_reuse_cap():
    x=Inputs(reuse_fraction=1)
    r=calculate(x)
    assert r['freshwater_kld']+r['reuse_kld']==pytest.approx(r['water_kld'])
    assert r['reuse_kld']<=r['sewage_kld']
    assert r['glr_kl']+r['oht_kl']==pytest.approx(r['storage_kl'])


def test_zero_efficiency_rejected():
    with pytest.raises(ValueError):
        calculate(Inputs(pump_efficiency=0))


def test_additional_fare_reduces_required_existing_allocation():
    a=funding(Funding(),Inputs())
    b=funding(Funding(proposed_incremental_fare_rs=1),Inputs())
    assert b['required_allocation_per_boarding_rs']<a['required_allocation_per_boarding_rs']
    assert a['break_even_boardings_at_allocated_rs'] is None


def test_passenger_km_only_when_enabled():
    a=funding(Funding(annual_passenger_km=1e8,proposed_rate_per_pkm_rs=1),Inputs())
    assert a['pkm_allocation_lakh']==0
