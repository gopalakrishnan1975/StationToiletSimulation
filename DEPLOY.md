# Deployment

Repository: gopalakrishnan1975/StationToiletSimulation (public).
Streamlit app: https://station-toilet-simulation.streamlit.app/
Branch: main; entry point: dashboard.py; Python: 3.12; dependencies: requirements.txt.

No secrets are required for planning or CSV mode. For approved database data, deploy data_api.py separately and set DATA_API_BASE/DATA_API_TOKEN in Streamlit's secret settings. DATABASE_URL exists only on the data API and importer hosts. See docs/DATABASE_INTEGRATION.md.

The deployed branch is followed automatically by Streamlit; a direct push may deploy before GitHub CI finishes. Local tests are run before release in this workflow. Future strict CI-gated promotion needs a separate release branch or other deployment control.

Generated documentation CI requires GitHub Actions enabled and the repository workflow token permitted to write contents on main. If repository policy blocks that bot push, the workflow will report it; generated docs can still be rebuilt locally and committed normally.
