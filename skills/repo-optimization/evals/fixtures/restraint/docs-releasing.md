# Releasing

1. Releases are cut from `main` only, never from a branch.
2. Update `CHANGELOG.md` under a new `## v<version>` heading; the release
   script refuses to run if the heading is missing.
3. Run `make release VERSION=1.4.0`. It tags `v1.4.0`, pushes the tag, and
   the `deploy` job in CI builds the image and rolls it to production.
4. Rollback is `make release VERSION=<previous>` with the same steps — it
   re-tags and redeploys the previous version; never `git revert` a release
   commit on `main`.
5. After deploy, watch `gateway_auth_failures_total` for ten minutes; a
   spike over 2% means roll back.
