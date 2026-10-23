from dataclasses import replace
from .queues import Config,run

def run_36_fixture_layout(layout='distributed',use_probability=.25,seed=42):
    c=Config(layout=layout,use_probability=use_probability,seed=seed)
    if layout=='central':
        c.stations=(300,);c.urinals=(9,);c.male_wc=(6,);c.female_wc=(18,);c.accessible_wc=(3,)
    elif layout=='hybrid':
        c.stations=(100,300,500);c.urinals=(2,5,2);c.male_wc=(1,4,1);c.female_wc=(4,10,4);c.accessible_wc=(1,1,1)
    else:
        c.stations=(100,300,500);c.urinals=(3,3,3);c.male_wc=(2,2,2);c.female_wc=(6,6,6);c.accessible_wc=(1,1,1)
    return run(c)
