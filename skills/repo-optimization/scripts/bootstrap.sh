#!/usr/bin/env bash
# Make `task` available in an environment that has no mise (Claude Code on
# the web, CI runners without mise-action, fresh containers). This is the one
# script invoked directly rather than through the Taskfile, because it is
# what makes the Taskfile runnable in the first place.
#
# Bundled with the repo-optimization skill: copy it to scripts/bootstrap.sh
# in the target repo (this repo symlinks it there).
#
# Order of preference:
#   1. `task` already on PATH            -> nothing to do
#   2. `mise` on PATH                    -> mise install (honours mise.toml)
#   3. mise installer reachable          -> install mise, then mise install
#   4. otherwise                         -> download the pinned `task` binary
#                                           from its GitHub release
# Idempotent and non-interactive. When $CLAUDE_ENV_FILE is set (SessionStart
# hook), the PATH change is persisted for the rest of the session.
set -euo pipefail

# Works from a copy at <repo>/scripts/bootstrap.sh, via a symlink, or from
# inside the skill directory: the repo is wherever git says it is.
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"
export PATH="$BIN_DIR:$PATH"

persist_path() {
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  fi
}

if command -v task >/dev/null 2>&1; then
  echo "bootstrap: task $(task --version) already available."
  persist_path
  exit 0
fi

if ! command -v mise >/dev/null 2>&1; then
  # Best effort: the installer host may be blocked by an egress policy.
  if curl -fsSL --max-time 20 https://mise.run -o "$BIN_DIR/mise-install.sh" 2>/dev/null; then
    MISE_INSTALL_PATH="$BIN_DIR/mise" sh "$BIN_DIR/mise-install.sh" >/dev/null 2>&1 || true
  fi
  rm -f "$BIN_DIR/mise-install.sh"
fi

if command -v mise >/dev/null 2>&1; then
  (cd "$REPO_ROOT" && mise install --yes) >/dev/null
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    (cd "$REPO_ROOT" && mise env -s bash) >> "$CLAUDE_ENV_FILE"
  fi
  echo "bootstrap: tools installed via mise from mise.toml."
  persist_path
  exit 0
fi

# Fallback: fetch the pinned task binary directly. Version comes from
# mise.toml (the only place versions live); a two-part pin gets a .0 patch.
VERSION="$(sed -nE 's/^task *= *"([^"]+)".*/\1/p' "$REPO_ROOT/mise.toml")"
case "$VERSION" in
  "") echo "bootstrap: no task version in mise.toml" >&2; exit 1 ;;
  *.*.*) ;;
  *) VERSION="${VERSION}.0" ;;
esac
case "$(uname -m)" in
  x86_64|amd64) ARCH=amd64 ;;
  aarch64|arm64) ARCH=arm64 ;;
  *) echo "bootstrap: unsupported architecture $(uname -m)" >&2; exit 1 ;;
esac
case "$(uname -s)" in
  Linux) OS=linux ;;
  Darwin) OS=darwin ;;
  *) echo "bootstrap: unsupported OS $(uname -s)" >&2; exit 1 ;;
esac
URL="https://github.com/go-task/task/releases/download/v${VERSION}/task_${OS}_${ARCH}.tar.gz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL --max-time 60 "$URL" -o "$TMP/task.tar.gz"
tar -xzf "$TMP/task.tar.gz" -C "$TMP" task
install -m 0755 "$TMP/task" "$BIN_DIR/task"
persist_path
echo "bootstrap: installed task v${VERSION} to $BIN_DIR (mise unavailable; python is whatever the environment provides)."
