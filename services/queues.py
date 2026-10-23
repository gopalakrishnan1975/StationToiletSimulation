"""Reproducible illustrative station sanitation discrete-event simulator. No external dependencies."""
import random, math, heapq, statistics, csv, argparse
from dataclasses import dataclass

@dataclass
class Config:
    platform_length_m:float=600
    boarding_margin_min:float=2
    passengers:int=1000
    trains:int=1
    headway_min:float=30
    wait_min:float=30
    access_min:float=45
    use_probability:float=.25
    male_fraction:float=.5
    urinal_fraction:float=.75
    walking_m_per_min:float=60
    seed:int=42
    layout:str='distributed'
    stations:tuple=(100,300,500)
    urinals:tuple=(3,3,3)
    male_wc:tuple=(2,2,2)
    female_wc:tuple=(4,4,4)
    accessible_wc:tuple=(1,1,1)
    accessibility_fraction:float=.03
    onboard_baseline:float=.30
    onboard_reduction_if_station_used:float=.60

SERVICE={'urinal':1.5,'male_wc':3.,'female_wc':4.,'accessible_wc':5.}

def run(cfg:Config):
    if cfg.passengers < 1 or cfg.trains < 1 or cfg.wait_min <= 0 or cfg.walking_m_per_min <= 0:
        raise ValueError('Positive passengers, trains, waiting time and walking speed required')
    if not 0 <= cfg.use_probability <= 1:
        raise ValueError('Use probability must be between zero and one')
    for counts in (cfg.urinals,cfg.male_wc,cfg.female_wc,cfg.accessible_wc):
        if len(counts) != len(cfg.stations) or any(v < 0 for v in counts):
            raise ValueError('Fixture counts must be nonnegative and match block positions')
    if any(not 0 <= loc <= cfg.platform_length_m for loc in cfg.stations):
        raise ValueError('Blocks must lie on platform')
    rng=random.Random(cfg.seed)
    locations=cfg.stations
    caps={'urinal':cfg.urinals,'male_wc':cfg.male_wc,'female_wc':cfg.female_wc,'accessible_wc':cfg.accessible_wc}
    # min-heaps of next-free time for each location/type
    servers={(j,k):[0.]*caps[k][j] for j in range(len(locations)) for k in SERVICE}
    for heap in servers.values(): heapq.heapify(heap)
    events=[]
    for train in range(cfg.trains):
        departure=train*cfg.headway_min+cfg.wait_min
        for _ in range(cfg.passengers):
            # Arrival times spread over the 30-minute window; position uniform is a scenario assumption
            arrival=train*cfg.headway_min+rng.uniform(0,cfg.wait_min)
            position=rng.uniform(0,cfg.platform_length_m)
            male=rng.random()<cfg.male_fraction
            accessible=rng.random()<cfg.accessibility_fraction
            kind='accessible_wc' if accessible else ('urinal' if male and rng.random()<cfg.urinal_fraction else 'male_wc' if male else 'female_wc')
            wants=rng.random()<cfg.use_probability
            if wants: events.append((arrival,position,departure,kind,train))
    events.sort()
    outcomes=[]
    for arrival,position,departure,kind,train in events:
        candidates=[]
        for j,loc in enumerate(locations):
            heap=servers[j,kind]
            if not heap: continue
            walk=abs(position-loc)/cfg.walking_m_per_min
            at=arrival+walk
            start=max(at,heap[0]); wait=start-at
            candidates.append((start+SERVICE[kind]+walk,walk,wait,j,start))
        if not candidates:
            outcomes.append(dict(kind=kind,served=0,walk=0,queue=0,train=train)); continue
        _,walk,wait,j,start=min(candidates)
        duration=max(.25,rng.lognormvariate(math.log(SERVICE[kind])-0.5*.3**2,.3))
        completed=start+duration
        served=completed+walk<=departure-cfg.boarding_margin_min # reserve 2 min for boarding
        if served:
            heap=servers[j,kind]; heapq.heapreplace(heap,completed)
        outcomes.append(dict(kind=kind,served=int(served),walk=walk,queue=wait,train=train))
    served=[o for o in outcomes if o['served']]
    n=cfg.passengers*cfg.trains
    pstation=len(served)/n
    onboard=cfg.onboard_baseline*(1-pstation*cfg.onboard_reduction_if_station_used)
    def percentile(a,p):
        if not a:return None
        a=sorted(a);return a[math.ceil(p*len(a))-1]
    return dict(layout=cfg.layout,passengers=n,attempts=len(outcomes),station_visits=len(served),station_visit_rate=round(pstation,4),unserved_attempts=len(outcomes)-len(served),mean_walk_min=round(statistics.mean([x['walk'] for x in served]),2) if served else None,p95_queue_min=round(percentile([x['queue'] for x in served],.95),2) if served else None,onboard_visits_expected=round(n*onboard,1),onboard_visits_avoided_expected=round(n*(cfg.onboard_baseline-onboard),1),by_type={k:dict(attempts=sum(x['kind']==k for x in outcomes),served=sum(x['served'] for x in outcomes if x['kind']==k),p95_queue_min=percentile([x['queue'] for x in served if x['kind']==k],.95)) for k in SERVICE})

def scenario(layout,prob,seed=42):
    c=Config(use_probability=prob,seed=seed,layout=layout)
    if layout=='central':
        c.stations=(300,);c.urinals=(9,);c.male_wc=(6,);c.female_wc=(12,);c.accessible_wc=(3,)
    elif layout=='hybrid':
        c.stations=(100,300,500);c.urinals=(2,5,2);c.male_wc=(1,4,1);c.female_wc=(3,6,3);c.accessible_wc=(1,1,1)
    return c

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--replications',type=int,default=100);parser.add_argument('--output',default='results.csv');args=parser.parse_args()
    rows=[]
    for p in [.15,.25,.40]:
        for layout in ['central','distributed','hybrid']:
            results=[run(scenario(layout,p,seed=100+i)) for i in range(args.replications)]
            row={'layout':layout,'toilet_use_probability':p,'replications':args.replications}
            for key in ['station_visits','unserved_attempts','mean_walk_min','p95_queue_min','onboard_visits_expected','onboard_visits_avoided_expected']:
                row[key]=round(statistics.mean(r[key] for r in results if r[key] is not None),2)
            rows.append(row)
    with open(args.output,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    for r in rows:print(r)
