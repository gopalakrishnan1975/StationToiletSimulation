from services.queues import Config,run
from services.experiments import allocation,compare_layouts

def test_conservation_and_reproducibility():
    c=Config(passengers=100,trains=2)
    a=run(c)
    assert a==run(c)
    assert a['attempts']==a['station_visits']+a['unserved_attempts']

def test_no_fixtures():
    a=run(Config(passengers=100,use_probability=1,urinals=(0,0,0),male_wc=(0,0,0),female_wc=(0,0,0),accessible_wc=(0,0,0)))
    assert a['station_visits']==0 and a['unserved_attempts']==100

def test_return_walk_deadline():
    a=run(Config(passengers=100,use_probability=1,wait_min=2))
    assert a['station_visits']==0

def test_equal_capacities():
    for total in range(40):
        assert sum(allocation(total,[1,2,1]))==total

def test_comparison():
    r=compare_layouts(50,.25,600,30,20,2,5,(9,6,18,3),3)
    assert len(r)==3
    assert all(x['Completed visits / train']<=50 for x in r)
