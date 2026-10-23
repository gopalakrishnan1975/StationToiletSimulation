from dataclasses import replace
from .infrastructure import Inputs,calculate
from .welfare import Policy,evaluate

def optimize(infra:Inputs,fee_candidates=(0,2,5,10),access_floor=.9,base_policy=None):
    options=[]
    for fee in fee_candidates:
        p=replace(base_policy or Policy(),tariff_wc=fee)
        w=evaluate(p,infra)
        baseline=infra.trains_day*infra.passengers_train*infra.station_use*(1-infra.urinal_share)
        access=w['realized_wc_day']/baseline if baseline else 1
        options.append({'fee':fee,'access_fraction':round(access,3),'financial_delta_lakh':w['incremental_financial_vs_free_lakh_year'],'social_delta_lakh':w['incremental_social_vs_free_lakh_year'],'feasible':access>=access_floor})
    eligible=[o for o in options if o['feasible']]
    return {'candidates':options,'social_welfare_choice':max(eligible,key=lambda o:o['social_delta_lakh']) if eligible else None,'financial_choice':max(eligible,key=lambda o:o['financial_delta_lakh']) if eligible else None}
