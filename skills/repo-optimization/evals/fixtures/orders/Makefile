.PHONY: test test-unit test-integration lint fmt typecheck build migrate ci

test: test-unit test-integration

test-unit:
	pytest tests/unit -q

test-integration:
	docker compose up -d db
	pytest tests/integration -q --maxfail=1

lint:
	ruff check orders tests
	npm run lint

fmt:
	ruff format orders tests

typecheck:
	mypy orders

build:
	npm run build
	docker build -t orders-service .

migrate:
	alembic upgrade head

ci: lint typecheck test
