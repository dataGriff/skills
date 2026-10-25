#!/usr/bin/env bash
# Eval fixture: rebuild the invoicer repo's git history from the snapshot.
set -euo pipefail
rm -- "$0"
stash=$(mktemp -d)
mv README.md pyproject.toml Makefile billing.py test_billing.py app.py deploy.sh "$stash/"
git init -q -b main

commit() { # author date message files...
  local who=$1 when=$2 msg=$3; shift 3
  for f in "$@"; do cp "$stash/$f" .; done
  git add "$@"
  local mail="$(printf %s "$who" | tr A-Z a-z)@acme.example"
  GIT_AUTHOR_NAME=$who GIT_AUTHOR_EMAIL=$mail GIT_AUTHOR_DATE=$when \
  GIT_COMMITTER_NAME=$who GIT_COMMITTER_EMAIL=$mail GIT_COMMITTER_DATE=$when \
    git commit -q -m "$msg"
}

commit Priya 2024-01-10T10:00:00 "Initial project skeleton" README.md pyproject.toml Makefile
commit Dave 2024-01-15T15:20:00 "Use banker's rounding for invoice totals

Finance requires ROUND_HALF_EVEN (ticket FIN-212): the ledger rounds
half-to-even, so half-up totals drifted by a penny on reconciliation." billing.py
commit Priya 2024-01-16T09:30:00 "Add billing tests" test_billing.py
sed 's/^RETRY_LIMIT = 7$/RETRY_LIMIT = 3/' "$stash/app.py" > app.py
git add app.py
GIT_AUTHOR_NAME=Dave GIT_AUTHOR_EMAIL=dave@acme.example GIT_AUTHOR_DATE=2024-02-01T11:00:00 \
GIT_COMMITTER_NAME=Dave GIT_COMMITTER_EMAIL=dave@acme.example GIT_COMMITTER_DATE=2024-02-01T11:00:00 \
  git commit -q -m "Push invoices to the payments API

Batches of 250: the provider rate-limits at 300 requests a minute."
commit Dave 2024-02-20T17:45:00 "deploy script" deploy.sh
commit Dave 2024-03-05T16:10:00 "bump retries" app.py
rm -rf "$stash"
