@echo off
cd /d "%~dp0"
if not exist "node_modules\vite\bin\vite.js" (
  echo Сначала установите зависимости: npm.cmd install
  exit /b 1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr LISTENING') do (
  echo Порт 3000 занят процессом %%a — завершаем...
  taskkill /PID %%a /F >nul 2>&1
)
node .\node_modules\vite\bin\vite.js
