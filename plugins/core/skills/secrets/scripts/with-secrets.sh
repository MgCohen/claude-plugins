#!/usr/bin/env sh
# Runs a command with the secrets from secrets.env in its environment.
# Usage: with-secrets.sh <command> [arguments]
# Set SECRETS_ENV_FILE to use another reference file.
set -eu

if [ "$#" -eq 0 ]; then
  echo "Usage: with-secrets.sh <command> [arguments]" >&2
  exit 2
fi

dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
env_file="${SECRETS_ENV_FILE:-$dir/../secrets.env}"
if [ ! -f "$env_file" ]; then
  echo "Reference file not found: $env_file" >&2
  exit 1
fi

# On Windows (Git Bash), a process that started before the token was set does not see it.
if [ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" ] && command -v powershell.exe >/dev/null 2>&1; then
  OP_SERVICE_ACCOUNT_TOKEN=$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('OP_SERVICE_ACCOUNT_TOKEN','User')" | tr -d '\r')
  export OP_SERVICE_ACCOUNT_TOKEN
fi
if [ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]; then
  echo "OP_SERVICE_ACCOUNT_TOKEN is not set. Ask the user to set it." >&2
  exit 1
fi

op_bin=$(command -v op || command -v op.exe || true)
if [ -z "$op_bin" ] && [ -n "${LOCALAPPDATA:-}" ]; then
  # winget puts op here on Windows.
  op_bin=$(ls "$LOCALAPPDATA"/Microsoft/WinGet/Packages/AgileBits.1Password.CLI_*/op.exe 2>/dev/null | head -n 1 || true)
fi
if [ -z "$op_bin" ] && [ "$(uname -s)" = "Linux" ]; then
  # Cloud sessions and Linux machines: install op the first time. It is one file and takes a few seconds.
  echo "op is not installed. Installing the 1Password CLI..." >&2
  sh "$dir/install-op-linux.sh" >&2
  op_bin=$(command -v op || true)
  [ -z "$op_bin" ] && [ -x "$HOME/.local/bin/op" ] && op_bin="$HOME/.local/bin/op"
fi
if [ -z "$op_bin" ]; then
  echo "op is not installed. Windows: winget install --id AgileBits.1Password.CLI --exact" >&2
  exit 1
fi

exec "$op_bin" run --env-file "$env_file" -- "$@"
