# Source review and changes (23 October 2026)

Reviewed all four ZIP source packages and all three original technical PDFs, plus results.csv, from the Station toilet simulation OneDrive folder. The two loose Python files are also represented in the v2 archive.

v1: queue proof of concept, 30 fixtures; synthetic CSV outputs. v2: infrastructure and cost model. v3: 36-fixture case, staffing, welfare and modular API. v4: fare funding and lecture narrative; queue code retained but absent from dashboard.

This iteration adds a queue/layout interface with equal-capacity comparisons, repeated simulations, Monte Carlo uncertainty, female/accessible queue statistics, exports and a return-walk boarding deadline. Adds input validation and edge-case tests. Corrects the roster display to follow selected cleaner establishment. Retains v4 engineering and policy calculations as illustrative, with costs anchored to 11 October assumptions rather than current quotations.

Important model limits: forward fixture reservations approximate FCFS and can miss gaps; predicted service means guide facility choice, actual service is stochastic; failed attempts do not consume fixture time. Queue percentiles describe completed users, not all demand. Separate unmet demand must be assessed alongside queue SLAs. Daily infrastructure uses potential demand and is deliberately not coupled to capacity-constrained throughput. No calibrated causal claim about onboard toilet use. Standalone microservice hosting and a full layout optimizer remain future work.
