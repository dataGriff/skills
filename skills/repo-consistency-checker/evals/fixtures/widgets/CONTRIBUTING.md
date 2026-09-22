# Contributing

## Setup

Requires Python 3.11. Create a virtualenv and install the dev tools:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy `settings.yaml` to `settings.local.yaml` and adjust the port if 8080
is taken on your machine — the service listens on port 8080 by default.

## Style

We lint with ruff; run `make lint` before opening a PR. Keep functions
under 40 lines and prefer explicit exceptions over sentinel return values.

## Tests

Run `make test-unit`. Every bug fix needs a regression test in
`test_app.py`.
