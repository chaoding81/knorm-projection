param(
    [string]$Python = "",
    [switch]$Online,
    [string]$Venv = ""
)
$ErrorActionPreference = "Stop"
$taskInstallArgs = @((Join-Path $PSScriptRoot "install.py"))
if ($Online) { $taskInstallArgs += "--online" }
if ($Venv) { $taskInstallArgs += @("--venv", $Venv) }
if ($Python) {
    & $Python @taskInstallArgs
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 @taskInstallArgs
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python @taskInstallArgs
} else {
    throw "Install Python 3.12 x64 first, or pass -Python with the full interpreter path."
}
exit $LASTEXITCODE
