# Contributing

## How it works

Invoice totals apply the tax rate from INVOICER_TAX_RATE (default 0.20)
to the sum of the line amounts; totals are rounded half-to-even before
being pushed to the payments provider.

## Checks

Run `make check` before you push; it runs the linter and the tests. The
deploy procedure is in [docs/deploy.md](docs/deploy.md).
