import json
from dataclasses import asdict
from services.experiments import compare_layouts
import streamlit as st
import pandas as pd
from services.infrastructure import Inputs,calculate
from services.welfare import Policy,evaluate,compare
from services.funding import Funding,evaluate as funding_eval
from services.premium import Premium,evaluate as premium_eval
from services.story import CHAPTERS
from services.roster import staffing
from services.optimization import optimize
st.set_page_config(page_title='AI Policy Laboratory | Railway Sanitation',layout='wide')
st.title('Station toilet simulation')
st.caption('An interactive senior-management teaching case; all price response, welfare benefits, infrastructure rates and costs are illustrative.')
with st.sidebar:
    st.subheader('Station and use')
    trains=st.slider('Trains/day',5,100,20)
    pax=st.slider('Boarding passengers/train',250,2500,1000,50)
    use=st.slider('Potential toilet use (%)',5,60,25)/100
    urinal=st.slider('Urinal share (%)',10,60,38)/100
    st.subheader('Behaviour and price')
    fee=st.slider('WC charge (₹)',0,20,5)
    elasticity=st.slider('Demand-response coefficient',-1.5,0.,-.25,.05)
    disutility=st.slider('Lost use social value (₹)',0,100,12)
    diversion=st.slider('Discouraged users going onboard (%)',0,100,30)/100
    st.subheader('Facilities and operating policy')
    storage=st.slider('Water autonomy (days)',.5,3.,1.25,.25)
    cleaners=st.slider('Cleaners',6,40,18)
    stp_energy=st.slider('STP kWh per kL',.3,3.,1.,.1)
    st.subheader('Fare budget')
    fare_alloc=st.slider('Existing fare revenue allocated / boarding (₹)',0.,10.,2.2,.1)
    newfare=st.slider('Proposed additional fare / boarding (₹)',0.,10.,0.,.1)
    nonfare=st.slider('Commercial / other funds (₹ lakh/year)',0.,200.,0.,5.)
x=Inputs(trains_day=trains,passengers_train=pax,station_use=use,urinal_share=urinal,storage_days=storage,cleaners=cleaners,stp_kwh_kl=stp_energy)
annual=trains*pax*365
f=Funding(annual_boardings=annual,allocated_existing_fare_rs=fare_alloc,proposed_incremental_fare_rs=newfare,nonfare_revenue_lakh=nonfare)
p=Policy(tariff_wc=fee,demand_response=elasticity,value_of_visit_rs=disutility,onboard_diversion=diversion)
inf=calculate(x); w=evaluate(p,x); fin=funding_eval(f,x)
st.metric('Basic sanitation: annual full economic cost (₹ lakh)',fin['annual_funding_need_lakh'])
st.metric('Required budget allocation per boarding passenger (₹)',fin['required_allocation_per_boarding_rs'])
tabs=st.tabs(['🚉 Queues & layout','🎤 Lecture story','🧮 Fare-funded entitlement','🚻 Pricing & welfare','💧 Water + STP + electricity','🧹 Staff + operating cost','🎯 Choose a policy'])
with tabs[1]:
    chapter=st.slider('Move through the policy story',1,len(CHAPTERS),1)
    title,body=CHAPTERS[chapter-1]; st.header(title);st.write(body)
    st.progress(chapter/len(CHAPTERS));st.info('Discuss the management question, then adjust a relevant parameter in the next tabs.')
    st.write('**Learning loop:** Question → model → compare alternatives → uncertainty → pilot → policy revision')
with tabs[2]:
    a,b,c=st.columns(3)
    a.metric('Full cost/boarding',f"₹{fin['unit_cost_per_boarding_rs']}")
    b.metric('Fare + other allocations (₹L/year)',fin['all_funding_lakh'])
    c.metric('Budget surplus / gap (₹L/year)',fin['surplus_gap_lakh'])
    st.dataframe(pd.DataFrame([{'Metric':k,'Value':str(v)} for k,v in fin.items()]),hide_index=True,width='stretch')
    st.info('Allocating ₹2.20 of existing fare receipts is not equivalent to adding ₹2.20 to fare. Do not assume all passengers must be charged the same fare increment.')
with tabs[3]:
    a,b,c=st.columns(3);a.metric('Receipts ₹L/yr',w['gross_fees_lakh_year']);b.metric('WC visits deterred/day',w['discouraged_wc_day']);c.metric('Social welfare Δ ₹L/yr',w['incremental_social_vs_free_lakh_year'])
    df=pd.DataFrame([{'Policy':k,'WC visits/day':v['realized_wc_day'],'Net revenue ₹L':v['incremental_financial_vs_free_lakh_year'],'Social welfare Δ ₹L':v['incremental_social_vs_free_lakh_year']} for k,v in compare(x).items()]);st.dataframe(df,hide_index=True,width='stretch');st.bar_chart(df.set_index('Policy')[['Net revenue ₹L','Social welfare Δ ₹L']])
    st.warning('Tariff is a transfer, not a social gain; welfare evidence requires measured price responses and values.')
with tabs[4]:
    st.dataframe(pd.DataFrame([{'Metric':k,'Value':round(v,2) if isinstance(v,(int,float)) else v} for k,v in inf.items()]),hide_index=True,width='stretch')
with tabs[5]:
    st.json(staffing());st.write(f'Selected cleaner establishment for cost model: {cleaners} (reference coverage roster shown above).'); st.metric('Annual station OPEX ₹ lakh',round(inf['opex_lakh_year'],1));st.caption('Staffing model is a coverage proxy; validate breaks, work rules, peak staffing and SLAs.')
with tabs[6]:
    st.dataframe(pd.DataFrame(optimize(x)['candidates']),hide_index=True,width='stretch')
    st.subheader('Optional premium facility: incremental economics')
    st.json(premium_eval(Premium()));st.caption('Do not remove free basic capacity to generate premium receipts.')
st.download_button('Download this scenario as JSON',data=json.dumps({'inputs':asdict(x),'policy':asdict(p),'funding_inputs':asdict(f),'infrastructure':inf,'welfare':w,'funding':fin},indent=2),file_name='station_policy_scenario.json',mime='application/json')

with tabs[0]:
    st.subheader('Compare toilet locations and fixture capacity')
    st.caption('Each layout has equal total fixtures. Demand is generated per train; overlapping train windows share queues. Utility sizing uses potential daily demand, not capacity-constrained completed visits.')
    with st.form('queue_scenario'):
        a,b,c=st.columns(3)
        length=a.number_input('Platform length (m)',100,1500,600,50)
        waiting=b.number_input('Passenger arrival window before departure (min)',5,120,30)
        headway=c.number_input('Train headway (min)',5,180,30)
        a,b,c=st.columns(3)
        ntrains=a.number_input('Trains in peak simulation',1,12,3)
        repeats=b.number_input('Simulation replications',5,100,20,5)
        target=c.number_input('Queue SLA (minutes)',1,30,3)
        a,b,c,d=st.columns(4)
        ur=a.number_input('Total urinals',0,90,9)
        mw=b.number_input('Total male WCs',0,90,6)
        fw=c.number_input('Total female WCs',0,120,18)
        aw=d.number_input('Total accessible WCs',0,30,3)
        run_button=st.form_submit_button('Run layout comparison',type='primary')
    if run_button:
        with st.spinner('Simulating passenger arrivals, walking and queues…'):
            rows=compare_layouts(pax,use,length,waiting,headway,ntrains,repeats,(ur,mw,fw,aw),target)
        st.session_state['queue_results']=rows
    if 'queue_results' in st.session_state:
        rows=st.session_state['queue_results']
        df=pd.DataFrame(rows)
        st.dataframe(df,hide_index=True,width='stretch')
        st.bar_chart(df.set_index('Layout')[['Completed visits / train','Unmet attempts / train']])
        st.download_button('Download queue comparison CSV',df.to_csv(index=False),'queue_comparison.csv','text/csv')
        st.caption('Queue statistics cover completed users; unmet demand is reported separately. P95 figures are averaged across replications; CI is a normal-approximation Monte Carlo interval for mean completed visits. Onboard displacement is hypothetical.')
