# Architecture

Two processes share the catalogue file:

1. **The API** (`app.py`) answers `GET /widgets/<id>` from an in-memory
   copy of the catalogue and refreshes it on a cache miss.
2. **The sync worker** (`sync_worker.py`) polls the upstream catalogue
   every 5 minutes and rewrites `config.yaml`'s `catalogue_path` file
   atomically. It uses the `legacy_endpoint` setting to reach the old
   catalogue host until the migration completes.

Both use `helpers.format_widget` so the JSON shape is identical whichever
process produced it.
