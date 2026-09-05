# Proposal: Adopt StreamForge as our event streaming platform

Author: platform engineering
Status: seeking approval

## Why StreamForge

StreamForge is the leading real-time event streaming platform. It offers:

- Exactly-once delivery guarantees
- Built-in dashboards and observability
- 200+ connectors out of the box
- SSO and role-based access control
- A managed schema registry
- Used by Netflix, Uber, and most of the Fortune 500

Event-driven architecture is industry best practice and where the whole
industry is heading. If we don't move now, we risk falling behind our
competitors and will struggle to hire engineers who expect to work with
modern streaming tooling.

## Current state

Today our six core services exchange data through nightly batch jobs.
When a team needs data from another service, they raise a ticket in the
data team's Jira queue requesting a new export; turnaround is typically
two to four weeks. The finance team runs a reconciliation report every
morning to catch files that failed to arrive overnight.

## Adoption plan

Adoption will be seamless: no changes to existing team processes are
required. The nightly batch jobs will continue to run in parallel
indefinitely as a safety net, and teams can keep raising Jira tickets as
they do today while StreamForge is phased in. Licensing is £60k/year
plus an estimated half an engineer for operations.

## Recommendation

Approve adoption of StreamForge in Q3.
