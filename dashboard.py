import hashlib
import json
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from services.experiments import compare_layouts
from services.infrastructure import Inputs, calculate
from services.welfare import Policy, evaluate, compare
from services.funding import Funding, evaluate as funding_eval
from services.premium import Premium, evaluate as premium_eval
from services.story import CHAPTERS
from services.roster import staffing
from services.optimization import optimize
from services.data import parse_csv, normalized_calls, provenance
from services.api_client import fetch_calls

VERSION='6.0.0'
st.set_page_config(page_title='Station toilet simulation',layout='wide')
st.title('Station toilet simulation')
st.caption(f'Version {VERSION} · Planning and pilot evaluation. Engineering costs and behavioural effects remain illustrative; imported train data do not validate those assumptions.')
with st.sidebar:
    st.subheader('Station and use')
    trains=st.slider('Trains/day',5,100,20)
    pax=st.slider('Boarding passengers/train',250,2500,1000,50)
    use=st.slider('Potential toilet use (%)',0,100,25)/100
    urinal=st.slider('Urinal share of all visits (%)',0.0,48.5,37.5,.5)/100
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

x=Inputs(trains_day=trains,passengers_train=pax,station_use=use,urinal_share=urinal,
         storage_days=storage,cleaners=cleaners,stp_kwh_kl=stp_energy)
f=Funding(annual_boardings=trains*pax*365,allocated_existing_fare_rs=fare_alloc,
          proposed_incremental_fare_rs=newfare,nonfare_revenue_lakh=nonfare)
p=Policy(tariff_wc=fee,demand_response=elasticity,value_of_visit_rs=disutility,onboard_diversion=diversion)
inf=calculate(x); w=evaluate(p,x); fin=funding_eval(f,x)
a,b=st.columns(2)
a.metric('Annual full economic cost (₹ lakh)',fin['annual_funding_need_lakh'])
b.metric('Required existing-fare allocation per boarding (₹)',fin['required_allocation_per_boarding_rs'])
tabs=st.tabs(['Queues & layout','Real data','Funding','Pricing & welfare','Water & energy','Staff & cost','Policy options','Technical guide','Lecture story'])

# Process imports before queue scenarios so loaded records are usable in the same session.
with tabs[1]:
    st.subheader('Connect station observations')
    st.write('Load one station, platform and Indian service date. Required columns: station_code, platform, train_id, departure_at (+05:30), boarding_passengers. Optional: all four fixture attempt counts. Completed visits alone do not measure unmet demand.')
    sample=(Path(__file__).parent/'data/example_train_calls.csv').read_bytes()
    st.download_button('Download CSV template (synthetic example)',sample,'example_train_calls.csv','text/csv')
    uploaded=st.file_uploader('Station train-call CSV (aggregate counts only)',type=['csv'])
    if uploaded is not None:
        digest=hashlib.sha256(uploaded.getvalue()).hexdigest()
        if digest!=st.session_state.get('loaded_upload'):
            try:
                calls=parse_csv(uploaded.getvalue())
                st.session_state['observed_calls']=calls
                st.session_state['data_provenance']=provenance(calls,'Uploaded CSV — source not independently verified')
                st.session_state['loaded_upload']=digest
            except (ValueError,UnicodeError):
                st.session_state.pop('observed_calls',None)
                st.session_state.pop('data_provenance',None)
                st.error('CSV failed validation. Check the template, timezone, duplicate calls, counts and one-platform/date rule.')
    if st.button('Load synthetic example'):
        calls=parse_csv(sample)
        st.session_state['observed_calls']=calls
        st.session_state['data_provenance']=provenance(calls,'Synthetic demonstration — not real station data')
    st.subheader('Approved data API')
    def setting(name):
        try:
            return st.secrets.get(name,os.environ.get(name,''))
        except FileNotFoundError:
            return os.environ.get(name,'')
    api_base=setting('DATA_API_BASE'); token=setting('DATA_API_TOKEN')
    if api_base and token:
        with st.form('api_data'):
            station=st.text_input('Station code',value='SC')
            platform=st.text_input('Platform',value='1')
            day=st.date_input('Service date',value=date(2026,10,23))
            fetch=st.form_submit_button('Fetch approved station data')
        if fetch:
            try:
                calls=fetch_calls(api_base,token,station.upper(),platform,day)
                st.session_state['observed_calls']=calls
                st.session_state['data_provenance']=provenance(calls,'Configured aggregate database API')
            except ValueError:
                st.session_state.pop('observed_calls',None)
                st.session_state.pop('data_provenance',None)
                st.error('Could not load valid station records. Check service access and data quality; previous data were cleared.')
    else:
        st.info('Live database API is not configured. The app can use CSV today. An administrator must set DATA_API_BASE and DATA_API_TOKEN in deployment secrets after deploying the separate data API.')
    if st.session_state.get('observed_calls'):
        st.json(st.session_state['data_provenance'])
        st.success('Records are ready for Queues & layout. Utilities, finance and pricing still use the sidebar planning assumptions.')
        if st.button('Clear loaded data'):
            for key in ('observed_calls','data_provenance','queue_results','queue_fingerprint'):
                st.session_state.pop(key,None)
            st.rerun()
    st.caption('Data stays in this session; the dashboard does not insert uploaded records into a database. Use approved aggregate records only. Do not upload names, PNRs, medical information or credentials.')

with tabs[0]:
    st.subheader('Compare toilet locations and fixture capacity')
    st.caption('Equal total fixtures across layouts. Chronological arrivals join FCFS queues after walking to the facility; service plus return walk must fit before boarding.')
    data_available=bool(st.session_state.get('observed_calls'))
    source=st.radio('Queue demand source',['Planning scenario','Loaded train calls'],horizontal=True)
    if source=='Loaded train calls' and not data_available:
        st.info('Load a CSV or API dataset in Real data first. No synthetic fallback will run for this selection.')
    with st.form('queue_scenario'):
        a,b,c=st.columns(3)
        length=a.number_input('Platform length (m)',100,1500,600,50)
        waiting=b.number_input('Passenger arrival window before departure (min)',5,120,30)
        headway=c.number_input('Train headway (min)',5,180,30)
        a,b,c=st.columns(3)
        ntrains=a.number_input('Trains in peak simulation',1,12,3)
        repeats=b.number_input('Simulation replications',5,100,20,5)
        target=c.number_input('Queue SLA (minutes)',1,30,3)
        service_floor=st.slider('Minimum demand served (%)',50,100,90)/100
        a,b,c,d=st.columns(4)
        ur=a.number_input('Total urinals',0,90,9)
        mw=b.number_input('Total male WCs',0,90,6)
        fw=c.number_input('Total female WCs',0,120,18)
        aw=d.number_input('Total accessible WCs',0,30,3)
        run_button=st.form_submit_button('Run layout comparison',type='primary')
    calls=normalized_calls(st.session_state['observed_calls']) if source=='Loaded train calls' and data_available else ()
    inputs=dict(passengers=pax,use=use,length=length,waiting=waiting,headway=headway,trains=ntrains,
                repeats=repeats,counts=(ur,mw,fw,aw),target=target,urinal_share=urinal,
                service_floor=service_floor,calls=calls)
    fingerprint=hashlib.sha256(json.dumps({'inputs':inputs,'source':source,'version':VERSION},sort_keys=True).encode()).hexdigest()
    if run_button and (source=='Planning scenario' or data_available):
        try:
            with st.spinner('Simulating arrivals, walks and fixture queues…'):
                rows=compare_layouts(**inputs)
            st.session_state['queue_results']=rows
            st.session_state['queue_fingerprint']=fingerprint
            st.session_state['queue_provenance']=st.session_state.get('data_provenance') if calls else {'source':'Synthetic planning scenario'}
        except ValueError as exc:
            st.error(str(exc))
            st.session_state.pop('queue_results',None)
    if 'queue_results' in st.session_state:
        if st.session_state.get('queue_fingerprint')!=fingerprint:
            st.warning('Queue inputs changed. Run layout comparison again; previous results are hidden.')
        else:
            df=pd.DataFrame(st.session_state['queue_results'])
            st.dataframe(df,hide_index=True,width='stretch')
            st.bar_chart(df.set_index('Layout')[['Completed visits / train','Unmet attempts / train']])
            st.download_button('Download queue comparison CSV',df.to_csv(index=False),'queue_comparison.csv','text/csv')
            st.caption('Queue P95s describe completed users and are averaged across replications. The overall service target also checks unmet demand. Confidence intervals measure Monte Carlo sampling only, not model uncertainty.')
    if calls:
        st.caption('Loaded calls supply actual departure spacing and boardings; observed fixture attempts override assumed use when present. Arrival-window, walking and duration assumptions remain synthetic. Headway and train-count controls apply only to planning scenarios.')

with tabs[2]:
    st.dataframe(pd.DataFrame([{'Metric':k,'Value':str(v)} for k,v in fin.items()]),hide_index=True,width='stretch')
    st.info('An allocation from existing fares is a budget transfer. A proposed fare increment is shown separately. Required existing allocation is net of additional fare and other funding.')
with tabs[3]:
    a,b,c=st.columns(3)
    a.metric('Receipts ₹ lakh/year',w['gross_fees_lakh_year'])
    b.metric('WC visits deterred/day',w['discouraged_wc_day'])
    c.metric('Social welfare Δ ₹ lakh/year',w['incremental_social_vs_free_lakh_year'])
    df=pd.DataFrame([{'Policy':k,'WC visits/day':v['realized_wc_day'],'Financial Δ ₹ lakh':v['incremental_financial_vs_free_lakh_year'],'Social Δ ₹ lakh':v['incremental_social_vs_free_lakh_year']} for k,v in compare(x,p).items()])
    st.dataframe(df,hide_index=True,width='stretch')
    st.bar_chart(df.set_index('Policy')[['Financial Δ ₹ lakh','Social Δ ₹ lakh']])
    st.caption('All alternatives use the current behavioural settings. Exempt users retain free-access demand. Receipts are transfers and are excluded from social welfare.')
with tabs[4]:
    st.dataframe(pd.DataFrame([{'Metric':k,'Value':round(v,2)} for k,v in inf.items()]),hide_index=True,width='stretch')
    st.warning('Daily sizing only: hourly storage routing, STP influent/effluent quality, outages, cleaning closures and detailed equipment selection are not modeled.')
with tabs[5]:
    roster=staffing()
    st.json(roster)
    st.write(f'Selected cleaner establishment used in costs: {cleaners}; reference roster requirement: {roster["cleaner_establishment"]}.')
    if cleaners<roster['cleaner_establishment']:
        st.warning('Selected cleaners are below the reference coverage roster. The model does not establish SLA-compliant staffing.')
    st.metric('Annual station OPEX ₹ lakh',round(inf['opex_lakh_year'],2))
with tabs[6]:
    opt=optimize(x,base_policy=p)
    st.dataframe(pd.DataFrame(opt['candidates']),hide_index=True,width='stretch')
    st.write('Social-welfare choice among candidates:',opt['social_welfare_choice'])
    st.caption('This is a tariff candidate search under a 90% demand-retention floor, not a full fixture, layout or workforce optimizer.')
    st.json(premium_eval(Premium()))
with tabs[7]:
    guide=Path(__file__).parent/'docs/TECHNICAL_GUIDE.md'
    if guide.exists():
        st.markdown(guide.read_text())
    st.link_button('Code, design and validation documents','https://github.com/gopalakrishnan1975/StationToiletSimulation')
with tabs[8]:
    chapter=st.slider('Move through the policy story',1,len(CHAPTERS),1)
    title,body=CHAPTERS[chapter-1]
    st.header(title);st.write(body);st.progress(chapter/len(CHAPTERS))

export={'version':VERSION,'infrastructure_inputs':asdict(x),'policy_inputs':asdict(p),'funding_inputs':asdict(f),
        'infrastructure':inf,'welfare':w,'funding':fin}
if st.session_state.get('queue_fingerprint')==fingerprint and 'queue_results' in st.session_state:
    export.update(queue_inputs={k:v for k,v in inputs.items() if k!='calls'},queue_results=st.session_state['queue_results'],
                  queue_provenance=st.session_state.get('queue_provenance'),scenario_fingerprint=fingerprint)
st.download_button('Download scenario and current results as JSON',json.dumps(export,indent=2),'station_policy_scenario.json','application/json')
