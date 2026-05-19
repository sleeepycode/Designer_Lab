@echo off
cd /d "%~dp0"
echo Установка зависимостей...
call npm.cmd install
if errorlevel 1 (
  echo.
  echo Ошибка установки. Запустите этот файл двойным щелчком или из cmd.exe, не из PowerShell.
  pause
  exit /b 1
)
if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo Создан файл .env из .env.example
  )
)
echo.
echo Готово. Запустите start-dev.cmd
pause
