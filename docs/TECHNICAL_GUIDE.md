# Station Toilet Simulation — technical and operating guide

Version 6.0.0 · reviewed 23 October 2026

## What the application can establish

Compare central, distributed and hybrid toilet blocks with equal fixture totals; estimate completed visits, unmet attempts, walking and queue times; screen daily water, storage, pump and STP requirements; compare illustrative staffing, financing and tariff policies. These are planning scenarios, not sanctioned designs or measured causal effects.

The public Streamlit app runs Python domain modules locally. `api.py` exposes calculation endpoints for integration. `data_api.py` is a separate authenticated service over an aggregate database. Community Cloud hosts only the dashboard process; the API servers require their own hosts. Domain modules are separated but are not individually deployed microservices.

## Queue design and interpretation

Each train has a departure time and boarding population. In planning mode, headways and boardings are constant. Loaded train calls replace those with actual spacing and counts. If fixture attempt counts are supplied, those exact counts replace Bernoulli toilet-use demand; otherwise use probability remains an assumption.

Platform arrivals are uniform over the selected pre-departure window and origins are uniform along the platform. Passengers select the block with the earliest predicted completion including a return walk. They join the fixture queue only after walking there. Facility arrivals are processed chronologically with first-come-first-served service on the next available compatible fixture. People still walking do not reserve fixtures.

Service times are lognormal with log standard deviation 0.3 and illustrative means of 1.5 minutes (urinal), 3 (male WC), 4 (female WC) and 5 (accessible WC), with a 0.25-minute lower bound. Walking speed is 60 m/min and the boarding buffer is 2 minutes. A passenger balks when sampled service, queue and return walk cannot fit before boarding. This assumes knowledge of the sampled service duration; imperfect decision-making and missed trains are not modeled.

The default layout has 36 positions: 9 urinals, 6 male WCs, 18 female WCs and 3 accessible WCs. Blocks sit at the midpoint or at 1/6, 1/2 and 5/6 of platform length. Distributed allocation is equal; hybrid allocation uses 1:2:1 weights with largest-remainder integer rounding. Capacities sum to the same totals for every layout.

The demographic scenario assumes 50% male and 3% accessible routing. Urinal share is an aggregate fraction of all potential visits and is converted consistently to the conditional male-urinal probability, hence its 48.5% upper limit. These are simplified route choices, not exhaustive gender or accessibility modelling.

Results distinguish a queue-time SLA from an overall service target. The latter also requires the configured share of demand to be completed. Queue P95s describe completed users, and the reported number is the mean of replication-specific percentiles, not a pooled tail quantile. Zero demand or no completed subgroup is insufficient evidence of compliance. The confidence interval is a normal-approximation Monte Carlo interval for mean completions; it excludes calibration and model uncertainty. Common random seeds improve comparability, without guaranteeing perfect correlation across layouts.

Results are fingerprinted with version and inputs. Changing relevant inputs hides stale results until a new run. Form edits reach the server when submitted. Exports include current model inputs, outputs and dataset provenance, but omit raw imported train rows. Keep the original data separately to reproduce an observed-data run.

## Engineering and economics

Gross daily demand uses the sidebar's potential daily station demand, not capacity-constrained peak simulation throughput. Queue fixture changes do not automatically scale CAPEX or the staffing roster; costs retain the 36-fixture reference design. Imported peak train calls do not automatically become annual demand.

Daily water equals visits × weighted flush-and-handwashing litres plus cleaning water. Design reserve, storage autonomy and GLR/OHT split size daily storage. Pump duty uses head and efficiency. STP capacity uses sewage return, reserve and target loading, rounded to 5 KLD. Reuse is capped by both reclaimed sewage and eligible flushing demand. Hourly tank mass balance, peak equalization routing, quality compliance, cleaning closures, failures, standby operation and detailed BOQ design remain unimplemented. Equalization is a daily screening proxy.

OPEX includes loaded cleaner/supervisor wages, water, power and fixed maintenance/operator allowances. The staffing reference is 18 cleaners plus 4 supervisors; changing cleaners changes cost but does not prove shift coverage. The interface flags under-provision against that reference. All rates are illustrative October 2026 project assumptions, without updated vendor quotations.

Tariff response applies to non-exempt WC users; exempt demand remains at free-access level. Policy comparisons and candidate search use current sidebar behavioural assumptions. Receipts are transfers, excluded from social welfare; collection costs and discouraged access are resource/welfare effects. Premium economics use a separate illustrative case. The policy optimizer searches four tariff candidates under a 90% retained-demand floor, and does not optimize fixture counts or staff.

Funding separates allocations from existing fare receipts, a proposed additional fare and non-fare support. Required existing allocation is net of other financing. No-revenue break-even boardings is undefined (`null`), rather than an artificial large number. Passenger-km funding is counted only when explicitly enabled through the Funding model. Onboard displacement, health benefits and access values require field evidence; do not treat them as established cash savings.

## Operating the app

1. Set daily planning demand and cost/policy settings in the sidebar.
2. In **Queues & layout**, set platform length, arrival window, peak trains, fixture totals, replications and service targets, then run the comparison.
3. In **Real data**, download the CSV template, replace synthetic rows with approved aggregate records and upload. Choose **Loaded train calls** in the queue tab and rerun.
4. Use Funding, Pricing, Water & energy, Staff & cost and Policy options for separate planning calculations. A change in one module does not imply all other modules have been calibrated.
5. Export the current JSON scenario and queue CSV. Record the dataset hash and preserve the underlying approved source.

## Real data contract

One row per station/platform/train departure; one station, platform and Indian service date per dataset. Required fields are `station_code`, `platform`, `train_id`, `departure_at` (explicit +05:30 offset), and `boarding_passengers`. Optional fields are `attempts_urinal`, `attempts_male_wc`, `attempts_female_wc`, `attempts_accessible_wc`. Supply all four or none, consistently across the dataset. Attempts must not exceed boardings under the one-use-per-passenger model. Do not substitute served visits for attempts when demand is censored by queues.

Limits: 1 MB CSV/API body, 100 calls, 50,000 boardings per batch, and a simulation workload budget. Duplicate train/departure keys, mixed platforms/dates, negative counts, unknown columns and missing timezones are rejected. The uploaded dataset is held only in the current Streamlit session; the dashboard never writes it to a database or public repository.

A synthetic example demonstrates the interface; it is explicitly labelled and is not Secunderabad field data. Unverified uploads are not represented as authenticated real-world observations. The configured API may supply aggregate train-call records; no external Railway endpoint or credentials are bundled.

## Connect an API to a database

The dashboard sends a fixed authenticated HTTPS request to a separate FastAPI service. The service validates station/platform/date, executes a parameterized SELECT through SQLAlchemy and returns validated JSON. PostgreSQL credentials remain on the API host. Streamlit receives an API token, not a database password.

See [DATABASE_INTEGRATION.md](https://github.com/gopalakrishnan1975/StationToiletSimulation/blob/main/docs/DATABASE_INTEGRATION.md) for exact setup, the aggregate schema and read-only roles. SQL statements and arbitrary database targets are never accepted from the public UI. SQLite is for disposable integration tests; Community Cloud local files are not durable storage.

The data service is disabled unless a sufficiently long authentication token is configured. Use HTTPS at the hosting edge, a private database network and a SELECT-only account. An operator can ingest approved CSV batches offline using a separate writer account. HTTP endpoints do not create tables or write records. A shared token is a prototype integration control; multiple operational users require identity-based authorization, access scoping, audit logs, rate limits and managed secret rotation before production.

## Evidence and missing source access

The connected official GitHub `dataRepository` was empty on review. No live Railway database is connected. CRIS identifies NTES and an API platform, and its developer portal requires sign-in. This supports investigating an approved NTES feed, but does not prove this account has API access or that any particular endpoint supplies platform assignments, boardings or toilet counts.

Potential sources and the fields still needed:

| Source | Useful fields | Status |
|---|---|---|
| Authorized CRIS/NTES feed | Actual arrivals/departures and platform where exposed | Endpoint and entitlement needed |
| Approved PRS/UTS/divisional aggregates | Station and train boardings | Field definitions, aggregation and authorization needed |
| Local anonymous toilet counts/surveys | Attempts, completed use, service time, balking | New field measurements/export needed |
| Facility asset register | Chainage, fixture count, accessibility, closures | Site audit required |
| Water/power/STP meters and contracts | Flow, tank levels, energy, quality, wages and prices | Not connected; separate future adapters |

The first useful pilot is one platform and 14–28 representative days, including peak periods. Collect attempts as well as completions, observed service durations and actual departures. Timetables alone cannot calibrate sanitation demand or causal onboard substitution. No personal or medical records are required.

## Validation and automatic documentation

`python scripts/build_docs.py` runs the tests, records a validation matrix and reference outputs, and regenerates API/data schemas from executable models. The GitHub workflow is intended to run on code changes and publish refreshed generated documentation after successful tests. Streamlit follows the deployed `main` branch automatically; test success is not a release gate for that direct branch-following behaviour. Use a separate release branch and approval controls if deployment must be gated by CI.

This does not automatically invent source data, obtain permissions, calibrate assumptions or repair code using AI. Failed tests require a reviewed code fix.

## Official implementation references

- FastAPI SQL databases: https://fastapi.tiangolo.com/tutorial/sql-databases/
- Streamlit PostgreSQL: https://docs.streamlit.io/develop/tutorials/databases/postgresql
- Streamlit secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Streamlit persistence: https://docs.streamlit.io/develop/concepts/connections/connecting-to-data
- Streamlit updates from GitHub: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- CRIS NTES: https://cris.org.in/loadpage?page=proNTES
- CRIS project list/API platform: https://cris.org.in/loadpage?page=ProjectListPage

Original engineering and policy references remain in the earlier project papers. Current tariff authority and engineering standards require separate verification before operational decisions.
