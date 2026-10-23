# Streamlit Community Cloud deployment

Repository: gopalakrishnan1975/StationToiletSimulation (public).
Branch: main. Main file: dashboard.py. Python: 3.12.
Dependencies: requirements.txt. No secrets required for local computation.

Install locally: `pip install -r requirements-dev.txt`, then `python -m pytest -q` and `streamlit run dashboard.py`.

The interface uses modular Python domain services in a single Streamlit process for Community Cloud. The existing FastAPI gateway and Docker Compose are retained for a separate API/dashboard deployment; these are not independently hosted domain microservices. Streamlit Community Cloud alone does not host the FastAPI gateway.
