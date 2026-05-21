# Fix pg_hba.conf: remove UTF-8 BOM (breaks PostgreSQL start).
# Run as Administrator:
#   powershell -ExecutionPolicy Bypass -File scripts\fix_pg_hba.ps1

$ErrorActionPreference = "Stop"
$PgVersion = "16"
$dataDir = "C:\Program Files\PostgreSQL\$PgVersion\data"
$pgHba = Join-Path $dataDir "pg_hba.conf"
$backup = Join-Path $dataDir "pg_hba.conf.bak_20260522_015324"
$serviceName = "postgresql-x64-$PgVersion"

if (-not (Test-Path $backup)) {
    Write-Error "Backup not found: $backup"
}

# Restore original hba (scram-sha-256), no BOM
$content = [System.IO.File]::ReadAllText($backup)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($pgHba, $content, $utf8NoBom)
Write-Host "Restored pg_hba.conf from backup (no BOM)"

$pgCtl = "C:\Program Files\PostgreSQL\$PgVersion\bin\pg_ctl.exe"

# Stop duplicate processes (service vs pg_ctl conflict); ignore "no such process"
$ErrorActionPreference = "Continue"
& $pgCtl -D $dataDir stop -m fast 2>&1 | Out-Null
Start-Sleep -Seconds 2
Get-Process -Name "postgres" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$ErrorActionPreference = "Stop"

Restart-Service $serviceName -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

$st = (Get-Service $serviceName).Status
$portUp = $null -ne (Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)

Write-Host "Service status: $st"
Write-Host "Port 5432 listening: $portUp"

if (-not $portUp) {
    Write-Host "Trying pg_ctl start..."
    & $pgCtl -D $dataDir -w start
    Start-Sleep -Seconds 2
    $portUp = $null -ne (Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
}

if (-not $portUp) {
    Write-Error "PostgreSQL not running. See latest file in $dataDir\log"
}

Write-Host "OK. If password unknown, run: scripts\start_postgres_trust.ps1 then set password in psql."
