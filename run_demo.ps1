param(
    [int]$Port = 8502,
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectPath
$demoPython = Join-Path $projectPath ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $demoPython)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create .venv. Install Python 3.11 or newer and retry." }
    $Install = $true
}
if ($Install) {
    & $demoPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
}

Write-Host "Opening the guided demo at http://127.0.0.1:$Port/?demo=1"
Write-Host "Prepared scenarios need no model or API key. Press Ctrl+C to stop."
& $demoPython -m streamlit run app.py --server.address 127.0.0.1 --server.port $Port --server.headless false -- --demo
if ($LASTEXITCODE -ne 0) { throw "Demo failed to start. Try ./run_demo.ps1 -Install or choose another -Port." }
