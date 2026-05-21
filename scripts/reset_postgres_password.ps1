# Reset postgres password on Windows (PostgreSQL 16).
# Run as Administrator:
#   powershell -ExecutionPolicy Bypass -File scripts\reset_postgres_password.ps1

param(
    [string]$NewPassword = "postgres",
    [string]$PgVersion = "16"
)

$ErrorActionPreference = "Stop"
$pgData = "C:\Program Files\PostgreSQL\$PgVersion\data"
$pgHba = Join-Path $pgData "pg_hba.conf"
$psql = "C:\Program Files\PostgreSQL\$PgVersion\bin\psql.exe"
$serviceName = "postgresql-x64-$PgVersion"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

if (-not (Test-Path $pgHba)) {
    Write-Error "pg_hba.conf not found"
}

$backup = "$pgHba.bak_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $pgHba $backup
Write-Host "Backup: $backup"

$head = @"
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
"@
[System.IO.File]::WriteAllText($pgHba, $head, $utf8NoBom)
Write-Host "pg_hba.conf: trust for localhost (no BOM)"

Restart-Service $serviceName -Force
Start-Sleep -Seconds 3
if ((Get-Service $serviceName).Status -ne "Running") {
    Copy-Item $backup $pgHba -Force
    Write-Error "Service failed to start. Restored pg_hba from backup."
}

$env:PGPASSWORD = ""
& $psql -U postgres -h 127.0.0.1 -d postgres -c "ALTER USER postgres WITH PASSWORD '$NewPassword';"
if ($LASTEXITCODE -ne 0) {
    Copy-Item $backup $pgHba -Force
    Restart-Service $serviceName -Force
    Write-Error "ALTER USER failed"
}

Write-Host "Password set to: $NewPassword"

$restore = Get-ChildItem "$pgData\pg_hba.conf.bak_*" |
    Where-Object { $_.Name -notlike "*$(Split-Path $backup -Leaf)" } |
    Sort-Object LastWriteTime |
    Select-Object -First 1

if ($restore) {
    $orig = [System.IO.File]::ReadAllText($restore.FullName)
    [System.IO.File]::WriteAllText($pgHba, $orig, $utf8NoBom)
    Write-Host "Restored pg_hba from $($restore.Name)"
}

Restart-Service $serviceName -Force
Write-Host "Done. Run: python scripts\ensure_postgres_db.py"
