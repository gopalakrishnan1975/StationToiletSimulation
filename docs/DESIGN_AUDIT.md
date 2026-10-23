# Design verification and repair log

Reviewed 23 October 2026. Source baseline: GitHub commit e3bc394c809d7416535239ba7102030d8baaeb03.

| Requirement | Finding before review | Implemented behaviour | Evidence |
|---|---|---|---|
| FCFS at actual facility arrival | Platform-arrival order could reserve fixtures while still walking | Separate chronological platform and facility events | Deterministic two-passenger ordering regression |
| Boarding feasibility | Return walk was included in v5 but lacked explicit deterministic test | Service + return walk + margin enforced | Boundary/deadline tests |
| Capacity conservation | Equal-capacity layouts available | Retained largest-remainder allocation; 36-fixture default harmonized | Allocation and conservation tests |
| Queue SLA and unmet demand | A short queue could coexist with extensive rejected demand | Separate queue SLA and overall served-demand target | Saturated/zero-demand tests |
| Reproducibility | Same seeds, but exports omitted current queue state | Version/input fingerprint and queue result/provenance export | UI execution tests |
| Changed inputs | Old results could remain visible | Hidden until rerun | Stale-results regression |
| Pricing comparisons | Compare/optimizer used default behaviour | Use current behavioural settings | Zero-response comparison test |
| Exempt tariff demand | All users' demand fell with price | Exempt users retain baseline demand | Full-exemption test |
| Existing fare allocation | Other incremental financing not subtracted from required allocation | Net funding need; zero receipts gives undefined break-even | Funding tests |
| Real data | No external input path | Validated CSV, observed train-call queue mode, authenticated DB API | Import, API, DB and UI tests |
| Technical documentation | Historical v4 paper with later code gaps | Versioned guide, integration guide, schemas, generated test report | Documentation build script |
| Production microservices | Modular code behind one gateway | Added separately deployable data service; retained honest boundary | API entrypoints and guide |

## Still outside the implemented design

Hourly GLR/OHT and STP routing; equipment outages/cleaning; full fixture/layout/staff mixed-integer optimization; calibration by age and observed service durations; causal onboard sanitation effects; current quotations; actual PostgreSQL/CRIS credentials; row-level identity authorization and production operations. Queue fixture changes do not rescale the fixed-reference cost model. These are identified limitations, not passed design requirements.

No operational Railway records were copied into the public repository. The included CSV is synthetic.
