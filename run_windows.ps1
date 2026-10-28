#Requires -Version 5.0
$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot
$BACK = Join-Path $ROOT "backend"
$FRONT = Join-Path $ROOT "frontend"
$VENV = Join-Path $BACK ".venv"
$VPYTHON = Join-Path $VENV "Scripts\python.exe"
$VPIP = Join-Path $VENV "Scripts\pip.exe"
$VUVICORN = Join-Path $VENV "Scripts\uvicorn.exe"

Write-Host ""
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host "        RhythmIQ Admin Monitor" -ForegroundColor Cyan
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host ""

$PY = $null
$candidates = @("py -3.13", "py -3.12", "py -3.11", "py -3.10", "python3", "python")
foreach ($c in $candidates) {
    try {
        $parts = $c.Split(" ", 2)
        $cmd = $parts[0]
        $args = if ($parts.Count -gt 1) { @($parts[1]) } else { @() }
        $v = & $cmd @args -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($v -match "^3\.(10|11|12|13)$") {
            $PY = $c
            break
        }
    } catch {}
}

if (-not $PY) {
    Write-Host ""
    Write-Host "  ERROR: Python 3.10 to 3.13 not found." -ForegroundColor Red
    Write-Host "  Install Python 3.12 from https://www.python.org/downloads/windows/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "  Python found." -ForegroundColor Green

if (-not (Test-Path $VENV)) {
    $parts = $PY.Split(" ", 2)
    $cmd = $parts[0]
    $args = if ($parts.Count -gt 1) { @($parts[1]) } else { @() }
    & $cmd @args -m venv $VENV
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Could not create virtual environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

& $VPYTHON -m pip install --upgrade pip --quiet
Write-Host "  Installing backend dependencies..." -ForegroundColor Yellow
& $VPIP install -r "$BACK\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) {
    & $VPIP install -r "$BACK\requirements.txt"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Backend package installation failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

$ENV_FILE = Join-Path $BACK ".env"
if (-not (Test-Path $ENV_FILE)) {
    @"
APP_ENV=dev
SECRET_KEY=rhythmiq-secret-key-change-in-production
DATABASE_URL=sqlite:///./rhythm_iq.db
ACCESS_TOKEN_EXPIRE_MINUTES=1440
"@ | Set-Content -Path $ENV_FILE
}

Write-Host "  Preparing database..." -ForegroundColor Yellow
Push-Location $BACK
try {
    & $VPYTHON -c "from app.seed import seed_db; seed_db()"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Database setup failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} finally {
    Pop-Location
}

Write-Host "  Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location $FRONT
try {
    & npm install --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Frontend install failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "  Starting backend and frontend..." -ForegroundColor Green
Write-Host ""
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Login: admin@rhythmiq.io / admin123" -ForegroundColor DarkGray
Write-Host "  Stop: Ctrl+C in this window" -ForegroundColor DarkGray
Write-Host ""

$backendProcess = Start-Process -FilePath $VUVICORN -ArgumentList "app.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $BACK -PassThru
Start-Sleep -Seconds 2
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run dev -- --host 0.0.0.0" -WorkingDirectory $FRONT -PassThru

Write-Host "  Backend PID: $($backendProcess.Id)" -ForegroundColor Gray
Write-Host "  Frontend PID: $($frontendProcess.Id)" -ForegroundColor Gray
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    if ($backendProcess) { Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($frontendProcess) { Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue }
}
