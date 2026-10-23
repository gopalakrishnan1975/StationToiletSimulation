from dataclasses import dataclass
from math import ceil
@dataclass
class Inputs:
    trains_day:int=20
    passengers_train:int=1000
    station_use:float=.25
    urinal_share:float=.375
    urinal_l:float=2
    wc_l:float=6
    handwash_l:float=1.5
    cleaning_kl:float=3
    sewage_fraction:float=.90
    demand_growth:float=.20
    storage_days:float=1.25
    glr_share:float=.75
    pumping_hours:float=8
    pump_head_m:float=25
    pump_efficiency:float=.55
    peak_factor:float=2.5
    stp_utilization:float=.80
    reuse_fraction:float=.60
    electricity_rs_kwh:float=9
    freshwater_rs_kl:float=45
    stp_kwh_kl:float=1.0
    cleaners:int=18
    supervisors:int=4
    cleaner_monthly:float=30000
    supervisor_monthly:float=40000
    other_opex_lakh:float=31
    sanitation_base_capex_lakh:float=168
    glr_cost_lakh:float=14
    oht_cost_lakh:float=11
    pump_cost_lakh:float=5
    stp_cost_lakh:float=32
    eq_cost_lakh:float=6
    reuse_cost_lakh:float=6
    external_electrical_lakh:float=12
    pipes_cost_lakh:float=9
    instrumentation_lakh:float=5
    infra_contingency:float=.12

def calculate(x:Inputs):
    visits=x.trains_day*x.passengers_train*x.station_use
    water_kl=(visits*(x.urinal_share*x.urinal_l+(1-x.urinal_share)*x.wc_l+x.handwash_l))/1000+x.cleaning_kl
    design_water=water_kl*(1+x.demand_growth)
    storage=design_water*x.storage_days
    glr=storage*x.glr_share
    oht=storage-glr
    sewage=water_kl*x.sewage_fraction
    stp=ceil((sewage*(1+x.demand_growth)/x.stp_utilization)/5)*5
    eq=ceil(sewage*x.peak_factor/24*4) # 4-hour peak equalization upper planning proxy
    pump_flow=design_water/x.pumping_hours
    pump_kw=1000*9.81*(pump_flow/3600)*x.pump_head_m/(x.pump_efficiency*1000)
    daily_power=pump_kw*x.pumping_hours+x.stp_kwh_kl*sewage+18 # building lighting, exhaust allowance
    reclaimed=sewage*x.reuse_fraction
    # recycled water displaces only eligible non-potable demand; capped by flush demand
    flush=visits*(x.urinal_share*x.urinal_l+(1-x.urinal_share)*x.wc_l)/1000
    reuse=min(reclaimed,flush)
    freshwater=water_kl-reuse
    infra=sum([x.glr_cost_lakh,x.oht_cost_lakh,x.pump_cost_lakh,x.stp_cost_lakh,x.eq_cost_lakh,x.reuse_cost_lakh,x.external_electrical_lakh,x.pipes_cost_lakh,x.instrumentation_lakh])
    capex=x.sanitation_base_capex_lakh+infra*(1+x.infra_contingency)
    # 31 lakh baseline other opex includes old water/electric; replace these with calculated values
    labour=(x.cleaners*x.cleaner_monthly+x.supervisors*x.supervisor_monthly)*12/100000
    consumables_maintenance=24.0
    water_cost=freshwater*x.freshwater_rs_kl*365/100000
    power_cost=daily_power*x.electricity_rs_kwh*365/100000
    stp_ops=8.0 # lab, sludge, operator and maintenance provisional
    opex=labour+consumables_maintenance+water_cost+power_cost+stp_ops+7.0
    return dict(visits_day=visits,water_kld=water_kl,design_water_kld=design_water,storage_kl=storage,glr_kl=glr,oht_kl=oht,sewage_kld=sewage,stp_kld=stp,equalization_kl=eq,pump_flow_m3h=pump_flow,pump_kw=pump_kw,daily_kwh=daily_power,reuse_kld=reuse,freshwater_kld=freshwater,capex_lakh=capex,opex_lakh_year=opex,water_cost_lakh_year=water_cost,electricity_cost_lakh_year=power_cost)
if __name__=='__main__':
    for k,v in calculate(Inputs()).items():print(f'{k}: {v:.2f}')
