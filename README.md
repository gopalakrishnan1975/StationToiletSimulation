# Station toilet simulation

[Open the live simulator](https://station-toilet-simulation.streamlit.app/)

Version 6.0.0. Compare toilet layouts, chronological walking/FCFS queues, unmet demand, utility sizing, staffing, fare funding and tariff policy. Use a validated aggregate train-call CSV or configure an authenticated data API backed by PostgreSQL. No live Railway database is configured by default.

## Run

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run dashboard.py
```

Calculation API: `python -m uvicorn api:app --port 8000`.
Separate data API: `python -m uvicorn data_api:app --port 8001`.

## Documentation

- [Technical and operating guide](docs/TECHNICAL_GUIDE.md)
- [API ↔ database setup](docs/DATABASE_INTEGRATION.md)
- [Design audit and remaining gaps](docs/DESIGN_AUDIT.md)
- [Generated validation report](docs/generated/VALIDATION_REPORT.md)
- [Calculation API schema](docs/generated/calculation_openapi.json)
- [Data API schema](docs/generated/data_openapi.json)
- [Train-call data schema](docs/generated/train_call_schema.json)

Generate tested reference outputs and schemas: `python scripts/build_docs.py`.

The dashboard and calculation API reuse modular services; they are not five independently hosted domain microservices. The data API is separately deployable. Streamlit Community Cloud hosts the dashboard only. Keep API tokens and database URLs in host secrets, never GitHub.

All example demand, costs, engineering and welfare assumptions require field calibration. No sanctioned design, causal claim or live Railway entitlement is implied. See the design audit for known limitations.
