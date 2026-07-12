<#
Runs ExactBT from the project virtual environment.
Use -Split train or -Split validation. Final OOS stays locked unless the
explicit -UnlockFinalOos switch is supplied.
#>
param(
    [ValidateSet("train", "validation", "final_oos")]
    [string]$Split = "train",
    [switch]$UnlockFinalOos
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run setup.bat first."
}

$Arguments = @("-m", "exactbt.cli", "search", "--config", "config/search.yaml", "--split", $Split)
if ($UnlockFinalOos) { $Arguments += "--unlock-final-oos" }
& $Python @Arguments
