# widgets

A tiny HTTP service that serves widget records from a YAML catalogue.

## Setup

Requires Python 3.12. Create a virtualenv and install the dev tools:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy `settings.yaml` to `settings.local.yaml` and adjust the port if 8080
is taken on your machine — the service listens on port 8080 by default.

## Running the checks

```bash
make lint
make test
```

`make test` runs the unit tests with pytest. CI runs the same two targets
on every push.

## Behaviour

- `GET /widgets/<id>` returns the widget as JSON. A missing id returns an
  empty body with status 200 (the client treats an empty body as "not
  found").
- Upstream fetches are retried three times with exponential backoff before
  the request fails.
- Responses are cached in-process for `cache_ttl` seconds (see
  `settings.yaml`).

## Layout

```
app.py        request handling and the retry loop
helpers.py    formatting helpers shared by app.py and sync_worker.py
sync_worker.py  background job that refreshes the catalogue every 5 minutes
config.yaml   runtime settings
```
