@echo off
setlocal
where python >nul 2>nul
if %errorlevel% equ 0 (
    start "" python "%~dp0app.py"
    exit /b 0
)

set "LOCAL_EXE=%LOCALAPPDATA%\SmolLMAssistant\SmolLMAssistant.exe"
if exist "%LOCAL_EXE%" (
    start "" /D "%LOCALAPPDATA%\SmolLMAssistant" "%LOCAL_EXE%"
    exit /b 0
)

set "DIST_EXE=%~dp0dist\SmolLMAssistant\SmolLMAssistant.exe"
if exist "%DIST_EXE%" (
    start "" /D "%~dp0dist\SmolLMAssistant" "%DIST_EXE%"
    exit /b 0
)

python "%~dp0app.py"
exit /b 0
