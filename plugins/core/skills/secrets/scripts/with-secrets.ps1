# Runs a command with the secrets from secrets.env in its environment.
# Usage: & with-secrets.ps1 <command> [arguments]
# Set SECRETS_ENV_FILE to use another reference file.
$ErrorActionPreference = 'Stop'
if ($args.Count -eq 0) { throw 'Usage: with-secrets.ps1 <command> [arguments]' }

$envFile = if ($env:SECRETS_ENV_FILE) { $env:SECRETS_ENV_FILE } else { Join-Path (Split-Path -Parent $PSScriptRoot) 'secrets.env' }
if (-not (Test-Path $envFile)) { throw "Reference file not found: $envFile" }

# A process that started before the token was set does not see it. Read the user registry too.
if (-not $env:OP_SERVICE_ACCOUNT_TOKEN) {
    $env:OP_SERVICE_ACCOUNT_TOKEN = [Environment]::GetEnvironmentVariable('OP_SERVICE_ACCOUNT_TOKEN', 'User')
}
if (-not $env:OP_SERVICE_ACCOUNT_TOKEN) { throw 'OP_SERVICE_ACCOUNT_TOKEN is not set. Ask the user to set it as a user environment variable.' }

# winget adds op to the user PATH. A process that started before the install does not see it.
$op = Get-Command op -ErrorAction SilentlyContinue
if (-not $op) {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $op = Get-Command op -ErrorAction SilentlyContinue
}
if (-not $op) { throw 'op is not installed. Run: winget install --id AgileBits.1Password.CLI --exact' }

$command, $rest = $args
& $op.Source run --env-file $envFile -- $command @rest
exit $LASTEXITCODE
