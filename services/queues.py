"""Chronological discrete-event queues with walking, FCFS and boarding deadlines."""
import heapq
import math
import random
import statistics
from dataclasses import dataclass

SERVICE = {'urinal': 1.5, 'male_wc': 3., 'female_wc': 4., 'accessible_wc': 5.}

@dataclass
class Config:
    platform_length_m: float = 600
    boarding_margin_min: float = 2
    passengers: int = 1000
    trains: int = 1
    headway_min: float = 30
    wait_min: float = 30
    access_min: float = 45  # descriptive only; not a measured last-void interval
    use_probability: float = .25
    male_fraction: float = .5
    urinal_fraction: float = .75
    walking_m_per_min: float = 60
    seed: int = 42
    layout: str = 'distributed'
    stations: tuple = (100, 300, 500)
    urinals: tuple = (3, 3, 3)
    male_wc: tuple = (2, 2, 2)
    female_wc: tuple = (6, 6, 6)
    accessible_wc: tuple = (1, 1, 1)
    accessibility_fraction: float = .03
    onboard_baseline: float = .30
    onboard_reduction_if_station_used: float = .60
    # Optional normalized observed calls; each has departure_min, passengers, attempts by type.
    train_calls: tuple = ()


def percentile(values, p=.95):
    return sorted(values)[math.ceil(p * len(values))-1] if values else None


def validate(cfg):
    for name in ('platform_length_m', 'walking_m_per_min', 'wait_min', 'headway_min'):
        v = getattr(cfg, name)
        if not math.isfinite(v) or v <= 0:
            raise ValueError(f'{name} must be finite and positive')
    if cfg.boarding_margin_min < 0 or not math.isfinite(cfg.boarding_margin_min):
        raise ValueError('Boarding margin must be finite and nonnegative')
    for name in ('use_probability', 'male_fraction', 'urinal_fraction', 'accessibility_fraction', 'onboard_baseline', 'onboard_reduction_if_station_used'):
        if not 0 <= getattr(cfg, name) <= 1:
            raise ValueError(f'{name} must lie between zero and one')
    if cfg.passengers < 1 or cfg.trains < 1 or int(cfg.passengers) != cfg.passengers or int(cfg.trains) != cfg.trains:
        raise ValueError('Passengers and trains must be positive integers')
    if not cfg.stations or any(not 0 <= loc <= cfg.platform_length_m for loc in cfg.stations):
        raise ValueError('Blocks must lie on platform')
    for counts in (cfg.urinals, cfg.male_wc, cfg.female_wc, cfg.accessible_wc):
        if len(counts) != len(cfg.stations) or any(v < 0 or int(v) != v for v in counts):
            raise ValueError('Nonnegative integer fixture counts must match block positions')


def simulate(cfg, attempts):
    """Process platform arrivals then actual fixture arrivals in chronological order.

    Routing uses expected service time and currently committed fixture queues; people
    still walking are not reservations. At fixture arrival, deadline-infeasible users
    balk using their sampled service duration (perfect-knowledge planning assumption).
    """
    validate(cfg)
    caps = dict(zip(SERVICE, (cfg.urinals, cfg.male_wc, cfg.female_wc, cfg.accessible_wc)))
    servers = {(j, k): [float('-inf')]*caps[k][j] for j in range(len(cfg.stations)) for k in SERVICE}
    events = []
    for uid, item in enumerate(attempts):
        heapq.heappush(events, (item['arrival'], 1, uid, item))
    outcomes = []
    while events:
        now, phase, uid, item = heapq.heappop(events)
        kind = item['kind']
        if phase == 1:
            options = []
            for j, loc in enumerate(cfg.stations):
                heap = servers[j, kind]
                if heap:
                    walk = abs(item['position']-loc)/cfg.walking_m_per_min
                    expected_start = max(now+walk, heap[0])
                    options.append((expected_start+SERVICE[kind]+walk, walk, j))
            if not options:
                outcomes.append({**item, 'served': 0, 'walk': 0., 'queue': None, 'reason': 'no_fixture'})
                continue
            _, walk, j = min(options)
            item = {**item, 'walk': walk, 'block': j}
            heapq.heappush(events, (now+walk, 0, uid, item))
        else:
            heap = servers[item['block'], kind]
            start = max(now, heap[0])
            complete = start + item['duration']
            served = complete + item['walk'] <= item['departure']-cfg.boarding_margin_min
            if served:
                heapq.heapreplace(heap, complete)
            outcomes.append({**item, 'served': int(served), 'queue': start-now,
                             'service_start': start if served else None,
                             'service_end': complete if served else None,
                             'reason': 'completed' if served else 'boarding_deadline'})
    return outcomes


def run(cfg: Config):
    validate(cfg)
    rng = random.Random(cfg.seed)
    calls = cfg.train_calls or tuple({'departure_min': t*cfg.headway_min+cfg.wait_min, 'passengers': cfg.passengers} for t in range(cfg.trains))
    attempts = []
    n = sum(c['passengers'] for c in calls)
    for train, call in enumerate(calls):
        departure = call['departure_min']
        if call.get('attempts') is not None:
            kinds = [k for k in SERVICE for _ in range(call['attempts'][k])]
        else:
            kinds = []
            for _ in range(call['passengers']):
                male = rng.random() < cfg.male_fraction
                accessible = rng.random() < cfg.accessibility_fraction
                kind = 'accessible_wc' if accessible else ('urinal' if male and rng.random() < cfg.urinal_fraction else 'male_wc' if male else 'female_wc')
                if rng.random() < cfg.use_probability:
                    kinds.append(kind)
        for kind in kinds:
            attempts.append(dict(arrival=departure-cfg.wait_min+rng.uniform(0, cfg.wait_min),
                                 position=rng.uniform(0, cfg.platform_length_m), departure=departure,
                                 kind=kind, train=train,
                                 duration=max(.25, rng.lognormvariate(math.log(SERVICE[kind])-.5*.3**2, .3))))
    outcomes = simulate(cfg, attempts)
    served = [o for o in outcomes if o['served']]
    pstation = len(served)/n if n else 0
    avoided = len(served)*cfg.onboard_baseline*cfg.onboard_reduction_if_station_used
    return dict(layout=cfg.layout, passengers=n, attempts=len(outcomes), station_visits=len(served),
                station_visit_rate=pstation, unserved_attempts=len(outcomes)-len(served),
                mean_walk_min=statistics.mean(x['walk'] for x in served) if served else None,
                p95_queue_min=percentile([x['queue'] for x in served]),
                onboard_visits_expected=n*cfg.onboard_baseline-avoided,
                onboard_visits_avoided_expected=avoided,
                by_type={k: dict(attempts=sum(x['kind']==k for x in outcomes),
                                 served=sum(x['served'] for x in outcomes if x['kind']==k),
                                 p95_queue_min=percentile([x['queue'] for x in served if x['kind']==k])) for k in SERVICE})


def scenario(layout, prob, seed=42):
    c = Config(layout=layout, use_probability=prob, seed=seed)
    if layout == 'central':
        c.stations=(300,); c.urinals=(9,); c.male_wc=(6,); c.female_wc=(18,); c.accessible_wc=(3,)
    elif layout == 'hybrid':
        c.urinals=(2,5,2); c.male_wc=(1,4,1); c.female_wc=(4,10,4)
    elif layout != 'distributed':
        raise ValueError('Unknown layout')
    return c
