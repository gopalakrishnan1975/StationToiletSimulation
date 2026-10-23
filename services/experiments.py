"""Replicated equal-capacity spatial layout experiments."""
import math, statistics
from .queues import Config,run

def allocation(total, weights):
    raw=[total*w/sum(weights) for w in weights]
    result=[int(v) for v in raw]
    for i in sorted(range(len(weights)),key=lambda j:raw[j]-result[j],reverse=True)[:total-sum(result)]:
        result[i]+=1
    return tuple(result)

def compare_layouts(passengers,use,length,waiting,headway,trains,repeats,counts,target):
    rows=[]
    for layout,positions,weights in [('Central',[.5],[1]),('Distributed',[1/6,.5,5/6],[1,1,1]),('Hybrid',[1/6,.5,5/6],[1,2,1])]:
        results=[]
        for i in range(repeats):
            cfg=Config(passengers=passengers,trains=trains,platform_length_m=length,wait_min=waiting,headway_min=headway,use_probability=use,stations=tuple(length*p for p in positions),layout=layout,seed=100+i)
            for key,total in zip(('urinals','male_wc','female_wc','accessible_wc'),counts):
                setattr(cfg,key,allocation(total,weights))
            results.append(run(cfg))
        avg=lambda k:statistics.mean(r[k] for r in results if r[k] is not None) if any(r[k] is not None for r in results) else None
        visits=[r['station_visits']/trains for r in results]
        half=1.96*statistics.stdev(visits)/math.sqrt(repeats) if repeats>1 else 0
        row={'Layout':layout,'Completed visits / train':round(statistics.mean(visits),1),'95% CI half-width':round(half,1),'Unmet attempts / train':round(avg('unserved_attempts')/trains,1),'Mean walk (min)':avg('mean_walk_min'),'Mean P95 queue (min)':avg('p95_queue_min')}
        subgroup=[]
        for kind in ('female_wc','accessible_wc'):
            q=[r['by_type'][kind]['p95_queue_min'] for r in results if r['by_type'][kind]['p95_queue_min'] is not None]
            value=statistics.mean(q) if q else None
            row[kind+' P95 (min)']=round(value,2) if value is not None else None
            subgroup.append(value)
        row['Queue SLA']= 'Met' if all(v is not None and v<=target for v in subgroup) and row['Mean P95 queue (min)'] is not None and row['Mean P95 queue (min)']<=target else 'Not met / no completed sample'
        rows.append(row)
    return rows
