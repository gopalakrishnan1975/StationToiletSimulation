# API ↔ database integration

The database stores records. The API is the controlled doorway that validates requests and reads selected rows. The Streamlit app calls that doorway; it does not expose the database to browsers.

```mermaid
flowchart TD
  A["Approved aggregate CSV / ETL"] --> B["Operator import with writer role"]
  B --> C["PostgreSQL aggregate table"]
  C --> D["FastAPI data service: SELECT-only role"]
  D --> E["Streamlit server: HTTPS + bearer token"]
  E --> F["Validated train calls → queue simulation"]
```

## 1. Prepare a database

Use an existing approved PostgreSQL instance or a new development instance within your authorized network. The software does not provision one or incur hosting charges. SQLite is supported for local tests only.

On the API/ETL host, set a connection string in an environment secret:

```text
DATABASE_URL=postgresql+psycopg://READ_USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
DATA_API_TOKEN=<random-secret-at-least-32-characters>
```

These are placeholders, never credentials to commit. Encode reserved password characters in a connection URL. `sslmode=require` encrypts the transport; use `sslmode=verify-full` and the appropriate CA where supported to validate server identity. Never place a database password in a URL shown to users or in source control.

The prototype `sanitation_train_calls` table stores station code, platform, train ID, offset-aware departure timestamp as canonical text, service date, boarding count and a validated JSON payload. The composite primary key is station/platform/train/departure. This favours a small portable reference implementation. Production extensions should use typed timestamps/JSONB, controlled migrations, coverage metadata, source revisions, audit timestamps and source-keyed ingestion deduplication.

## 2. Import approved data with a separate writer account

From the repository root:

```bash
python -m pip install -r requirements.txt
# Set DATABASE_URL to the migration/writer role via your secret manager first.
python -m scripts.import_data approved_train_calls.csv --init
```

`--init` creates the prototype table. Omit it after initialization. Imports are validated and transactional; existing keys are rejected, not silently replaced. To correct source records, use an authorized data-management workflow. The public app cannot write to this table.

## 3. Grant API read access

An authorized database administrator can grant the API role `CONNECT` to the chosen database, `USAGE` on its schema and `SELECT` on `sanitation_train_calls`. Do not grant INSERT, UPDATE, DELETE, CREATE or administrative rights to this account. Configure a different DATABASE_URL on the API host using that read-only role; keep writer credentials on the trusted importer only.

```sql
-- Example names only; substitute approved database, schema and existing API role.
GRANT CONNECT ON DATABASE sanitation TO sanitation_reader;
GRANT USAGE ON SCHEMA public TO sanitation_reader;
GRANT SELECT ON TABLE public.sanitation_train_calls TO sanitation_reader;
```

## 4. Run the data API

```bash
python -m uvicorn data_api:app --host 0.0.0.0 --port 8001
```

Put HTTPS and network controls in front of it. The API accepts this request:

```http
GET /v1/data/train-calls?station=SC&platform=1&service_date=2026-10-23
Authorization: Bearer <configured-secret>
```

It returns `{ "schema_version": "1.0", "source": "configured station aggregate database", "records": [...] }`. No matches returns an empty list; the UI reports no valid dataset and does not reuse old data. Bad auth gives 401, unconfigured auth/database gives 503, invalid parameters/data gives 422. Error messages omit connection strings and SQL.

This endpoint selects a fixed table with bound values. It does not accept arbitrary SQL or expose a general database console. The response limits match the simulation contract. Add request throttling, identity/role checks and station-specific access restrictions before deployment with multiple users.

## 5. Connect Streamlit

In **Manage app → Settings → Secrets**, set:

```toml
DATA_API_BASE = "https://your-approved-api.example"
DATA_API_TOKEN = "the-same-long-random-secret"
```

The `.example` URL is a placeholder, not a deployed endpoint. Do not put DATABASE_URL in Streamlit for this API-mediated design. The UI then shows station/platform/date filters and a Fetch button in **Real data**. The server sends a timeout-limited HTTPS request, refuses redirects, limits response size and validates the returned records before using them. It does not cache records across user sessions.

The data service must be reachable from Streamlit's host. If an internal Railway API is restricted to the Railway network, use an approved gateway or host the app inside that network; do not expose an internal operational database to the Internet as a shortcut. Authentication to ChatGPT connectors does not automatically grant this public app access to OneDrive, CRIS or any Railway database.

## 6. Use real records in the simulator

Choose **Loaded train calls** in **Queues & layout** after fetching. Departure offsets, boardings and any measured attempt counts feed the simulation. Source hash and basis are displayed. The UI does not infer service-time distributions, water use, cleanliness or tariff elasticity from a timetable. Those require separate datasets and calibration.

## Deployment example

`docker-compose.yml` retains the calculation API and dashboard. A separately hosted `data_api:app` can be added as a third process/container with its own least-privilege DATABASE_URL and token. This is a separated data service; queue, welfare and engineering are still modules behind the calculation gateway rather than independently scaled domain services.

## Checks already implemented

SQLite import/read round-trip, transactional duplicate rejection, bound-query isolation, token checks, fail-closed configuration, invalid/duplicate CSV rejection, observed demand conservation, API queue requests and Streamlit observed-data execution are tested. An actual PostgreSQL network connection, CRIS authentication, production TLS and Railway data quality remain unverified until an approved endpoint is provided.
