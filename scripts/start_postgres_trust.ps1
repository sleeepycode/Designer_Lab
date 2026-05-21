# Stop stray Postgres, start with trust (no password) for password reset.
# Run as Administrator.

$ErrorActionPreference = "Continue"
$PgVersion = "16"
$dataDir = "C:\Program Files\PostgreSQL\$PgVersion\data"
$pgHba = Join-Path $dataDir "pg_hba.conf"
$pgCtl = "C:\Program Files\PostgreSQL\$PgVersion\bin\pg_ctl.exe"
$serviceName = "postgresql-x64-$PgVersion"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

Write-Host "Stopping PostgreSQL..."
& $pgCtl -D $dataDir stop -m fast 2>$null
Start-Sleep -Seconds 2
Get-Process -Name "postgres" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$trust = @"
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
"@
[System.IO.File]::WriteAllText($pgHba, $trust, $utf8NoBom)
Write-Host "pg_hba.conf = trust (no BOM)"

Write-Host "Starting via pg_ctl..."
& $pgCtl -D $dataDir -w start
Start-Sleep -Seconds 2

if (Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue) {
    Write-Host "Port 5432 is listening. Run in NEW terminal:"
    Write-Host '  cd "C:\Program Files\PostgreSQL\16\bin"'
    Write-Host '  .\psql.exe -U postgres -h 127.0.0.1 -d postgres'
    Write-Host "  ALTER USER postgres WITH PASSWORD 'postgres';"
    Write-Host "  \q"
    Write-Host "Then run: powershell -ExecutionPolicy Bypass -File scripts\fix_pg_hba.ps1"
} else {
    Write-Host "PostgreSQL did not start. Check log in $dataDir\log"
}
