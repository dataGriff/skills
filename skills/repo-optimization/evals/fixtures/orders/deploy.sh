#!/usr/bin/env bash
# Usage: ./deploy.sh <staging|prod> [--rollback]
set -euo pipefail
ENV="${1:?environment required}"
if [ "$ENV" = prod ] && [ -z "${DEPLOY_TOKEN:-}" ]; then
  echo "DEPLOY_TOKEN required for prod" >&2; exit 1
fi
if [ "${2:-}" = "--rollback" ]; then
  aws ecs update-service --cluster "$ENV" --service orders --task-definition orders:previous
  exit 0
fi
docker build -t orders-service .
docker tag orders-service "123456789.dkr.ecr.eu-west-1.amazonaws.com/orders:$ENV"
docker push "123456789.dkr.ecr.eu-west-1.amazonaws.com/orders:$ENV"
aws ecs update-service --cluster "$ENV" --service orders --force-new-deployment
