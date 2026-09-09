#!/usr/bin/env bash
# SessionStart hook for Claude Code on the web: the sandbox has no mise, so
# `task` (rule 1 in AGENTS.md) would be missing. Delegates to the same
# bootstrap script humans and CI can use.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
exec "$CLAUDE_PROJECT_DIR/scripts/bootstrap.sh"
