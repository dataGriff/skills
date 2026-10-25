#!/usr/bin/env bash
# Make GitHub enforce the repo's definition of green. Sets the merge
# settings (squash-only, delete head branches on merge, PR title/body as
# the squash commit) and a ruleset on the default branch that requires a
# pull request with the named CI checks green and blocks force pushes and
# deletions. Idempotent: re-running converges on the same state.
#
# Bundled with the repo-optimization skill: copy or symlink it into the
# target repo's scripts/ and call it from a task (this repo: `task setup:github`).
#
# Usage: github-settings.sh [--repo owner/name] [--checks ci,other]
#                           [--approvals N] [--dry-run]
#   --repo       default: the repo gh resolves from the current directory
#   --checks     status-check contexts that must pass before merge. For
#                GitHub Actions that is the job's `name:`, or its id when it
#                has none. Default "ci"; pass "" to require no checks.
#   --approvals  required approving reviews. Default 0, because a solo
#                maintainer cannot approve their own PR; raise it once
#                there are reviewers.
#   --dry-run    print the requests without sending them
#
# Requires the gh CLI authenticated with admin rights on the repo.
set -euo pipefail

REPO=""
CHECKS="ci"
APPROVALS=0
DRY_RUN=0
RULESET_NAME="default-branch"

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --checks) CHECKS="$2"; shift 2 ;;
    --approvals) APPROVALS="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "github-settings: unknown argument $1" >&2; exit 2 ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "github-settings: gh CLI not found (https://cli.github.com)." >&2
  exit 1
fi
if [ -z "$REPO" ]; then
  REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
fi

checks_json="[]"
if [ -n "$CHECKS" ]; then
  checks_json=""
  IFS=',' read -ra contexts <<< "$CHECKS"
  for context in "${contexts[@]}"; do
    checks_json="${checks_json}{\"context\":\"${context}\"},"
  done
  checks_json="[${checks_json%,}]"
fi

ruleset_json=$(cat <<EOF
{
  "name": "${RULESET_NAME}",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "required_linear_history"},
    {"type": "pull_request", "parameters": {
      "required_approving_review_count": ${APPROVALS},
      "dismiss_stale_reviews_on_push": true,
      "require_code_owner_review": false,
      "require_last_push_approval": false,
      "required_review_thread_resolution": true,
      "allowed_merge_methods": ["squash"]
    }},
    {"type": "required_status_checks", "parameters": {
      "strict_required_status_checks_policy": false,
      "do_not_enforce_on_create": false,
      "required_status_checks": ${checks_json}
    }}
  ]
}
EOF
)

merge_settings=(
  -F allow_squash_merge=true
  -F allow_merge_commit=false
  -F allow_rebase_merge=false
  -F delete_branch_on_merge=true
  -f squash_merge_commit_title=PR_TITLE
  -f squash_merge_commit_message=PR_BODY
)

if [ "$DRY_RUN" = 1 ]; then
  echo "github-settings: dry run for $REPO"
  echo "PATCH repos/$REPO ${merge_settings[*]}"
  echo "ruleset '$RULESET_NAME' (POST or PUT repos/$REPO/rulesets):"
  echo "$ruleset_json"
  exit 0
fi

echo "github-settings: $REPO — merge settings"
gh api -X PATCH "repos/$REPO" "${merge_settings[@]}" \
  --jq '"  squash=\(.allow_squash_merge) merge_commit=\(.allow_merge_commit) rebase=\(.allow_rebase_merge) delete_head_on_merge=\(.delete_branch_on_merge) squash_title=\(.squash_merge_commit_title)"'

existing_id="$(gh api "repos/$REPO/rulesets" --jq ".[] | select(.name == \"$RULESET_NAME\") | .id")"
if [ -n "$existing_id" ]; then
  echo "github-settings: $REPO — updating ruleset '$RULESET_NAME' (#$existing_id)"
  echo "$ruleset_json" | gh api -X PUT "repos/$REPO/rulesets/$existing_id" --input - --jq '"  enforcement=\(.enforcement) rules=\([.rules[].type] | join(","))"'
else
  echo "github-settings: $REPO — creating ruleset '$RULESET_NAME'"
  echo "$ruleset_json" | gh api -X POST "repos/$REPO/rulesets" --input - --jq '"  enforcement=\(.enforcement) rules=\([.rules[].type] | join(","))"'
fi
echo "github-settings: required checks: ${CHECKS:-none}; approvals: $APPROVALS"
