.PHONY: help build test lint ci proto migrate run release
PKG ?= ./...

help: ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk -F':.*##' '{printf "  %-10s %s\n", $$1, $$2}'

build: ## compile to bin/gateway
	go build -o bin/gateway ./cmd/gateway

test: ## unit tests (PKG=./internal/capture for one package)
	go test -race $(PKG)

lint: ## golangci-lint
	golangci-lint run ./...

ci: lint test ## what CI runs

proto: ## regenerate gen/ from proto/
	buf generate

migrate: ## apply migrations
	goose -dir migrations postgres "$$DATABASE_URL" up

run: ## local server
	docker compose up -d && go run ./cmd/gateway

release: ## tag and push a release: make release VERSION=1.4.0
	./hack/release.sh $(VERSION)
