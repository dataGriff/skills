# Runbook

## Queue backlog growing
1. Check worker count: `kubectl get pods -l app=notify-worker`.
2. Check Redis memory; if above 80%, scale workers before anything else.
3. If one channel dominates, pause it: `pnpm queue:pause <channel>`; resume
   with `pnpm queue:resume <channel>`.

## Provider outage
Flip the channel's `enabled` flag in LaunchDarkly. Messages queue and are
delivered when the flag is re-enabled. Do not delete jobs.

## Suspected PII leak in logs
Rotate the log sink credentials, open an incident, and grep the last 24 h of
logs for `@` and `+44`. The PII lint rule should have prevented it; find
the disabled rule and re-enable it.
