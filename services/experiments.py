"""Replicated equal-capacity spatial layout experiments."""
import math, statistics
from .queues import Config,run

def allocation(total, weights):
    raw=[total*w/sum(weights) for w in weights]
    result=[int(v) for v in raw]
    for i in sorted(range(len(weights)),key=lambda j:raw[j]-result[j],reverse=True)[:total-sum(result)]:
        result[i]+=1
    return tuple(result)

def compare_layouts(passengers,use,length,waiting,headway,trains,repeats,counts,target, *, urinal_share=.375, calls=(), service_floor=.9):
    if repeats < 2 or repeats > 100 or len(counts) != 4 or any(v<0 or int(v)!=v for v in counts):
        raise ValueError('Use 2–100 replications and four nonnegative integer fixture counts')
    if not 0<=service_floor<=1 or not 0<=urinal_share<=.485:
        raise ValueError('Invalid service floor or urinal share')
    if calls:
        trains=len(calls)
    if trains < 1 or passengers < 1 or (sum(c['passengers'] for c in calls) if calls else trains*passengers)*repeats>4_000_000:
        raise ValueError('Scenario too large; reduce passengers, trains or replications')
    rows=[]
    for layout,positions,weights in [('Central',[.5],[1]),('Distributed',[1/6,.5,5/6],[1,1,1]),('Hybrid',[1/6,.5,5/6],[1,2,1])]:
        results=[]
        for i in range(repeats):
            cfg=Config(passengers=passengers,trains=trains,platform_length_m=length,wait_min=waiting,headway_min=headway,use_probability=use,stations=tuple(length*p for p in positions),layout=layout,seed=100+i,urinal_fraction=urinal_share/(.5*.97),train_calls=calls)
            for key,total in zip(('urinals','male_wc','female_wc','accessible_wc'),counts):
                setattr(cfg,key,allocation(total,weights))
            results.append(run(cfg))
        avg=lambda k:statistics.mean(r[k] for r in results if r[k] is not None) if any(r[k] is not None for r in results) else None
        visits=[r['station_visits']/trains for r in results]
        half=1.96*statistics.stdev(visits)/math.sqrt(repeats) if repeats>1 else 0
        row={'Layout':layout,'Completed visits / train':round(statistics.mean(visits),1),'95% CI half-width':round(half,1),'Unmet attempts / train':round(avg('unserved_attempts')/trains,1),'Mean walk (min)':round(avg('mean_walk_min'),2) if avg('mean_walk_min') is not None else None,'Mean P95 queue (min)':round(avg('p95_queue_min'),2) if avg('p95_queue_min') is not None else None}
        subgroup=[]
        for kind in ('female_wc','accessible_wc'):
            q=[r['by_type'][kind]['p95_queue_min'] for r in results if r['by_type'][kind]['p95_queue_min'] is not None]
            value=statistics.mean(q) if q else None
            row[kind+' P95 (min)']=round(value,2) if value is not None else None
            subgroup.append(value)
        row['Queue SLA']=  'Met' if all(v is not None and v<=target for v in subgroup) and row['Mean P95 queue (min)'] is not None and row['Mean P95 queue (min)']<=target else 'Not met / no completed sample'
        attempted=sum(r['attempts'] for r in results)
        fraction=sum(r['station_visits'] for r in results)/attempted if attempted else None
        row['Demand served (%)']=round(100*fraction,1) if fraction is not None else None
        row['Overall service target']='Met' if row['Queue SLA']=='Met' and fraction is not None and fraction>=service_floor else 'Not met / insufficient demand'
        rows.append(row)
    return rows
