# invoicer

Generates monthly invoices for Acme customers and pushes them to the
payments provider.

## Setup

Get the `.env` file from Dave (ask in #invoicer-dev on Slack), put it in
the repo root, then:

```bash
pip install -e .
python app.py
```

## Deploying

Dave does the deploys. Ping him when something needs to go out.

## How it works

Invoice totals apply the tax rate from INVOICER_TAX_RATE (default 0.20)
to the sum of the line amounts; totals are rounded half-to-even before
being pushed to the payments provider.

## History

Previously we used Flask for the invoice API, but it is worth noting that
we switched to plain urllib in order to simply drop the dependency. The
old `flask_app.py` no longer exists. Basically the batching logic has not
changed since.
