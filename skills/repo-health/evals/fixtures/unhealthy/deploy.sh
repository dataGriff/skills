#!/usr/bin/env bash
set -euo pipefail
cd /home/dave/src/invoicer
export PAYMENT_API_KEY=$(aws ssm get-parameter --name /invoicer/prod/payment-api-key --with-decryption --query Parameter.Value --output text)
export INVOICER_DB_URL=$(aws ssm get-parameter --name /invoicer/prod/db-url --with-decryption --query Parameter.Value --output text)
tar czf /tmp/invoicer.tgz app.py billing.py pyproject.toml
scp /tmp/invoicer.tgz deploy@invoicer-prod-1.internal:/opt/invoicer/
ssh deploy@invoicer-prod-1.internal 'cd /opt/invoicer && tar xzf invoicer.tgz && sudo systemctl restart invoicer'
