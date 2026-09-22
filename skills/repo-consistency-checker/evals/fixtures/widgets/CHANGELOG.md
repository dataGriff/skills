# Changelog

## 0.3.0

- Removed the sync worker; the API now refreshes the catalogue on demand.
- Missing widgets now raise `WidgetNotFound` (HTTP 404) instead of
  returning an empty body.
- Upstream retries raised from 3 to 5.

## 0.2.0

- Added the sync worker (polls every 5 minutes).
- Added `legacy_endpoint` for the migration period.

## 0.1.0

- Initial release: `GET /widgets/<id>` with 3 retries, port 8080.
