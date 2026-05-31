@echo off
REM SpringForge CLI — lancement depuis l'environnement virtuel
set ROOT=%~dp0..
call "%ROOT%\.venv\Scripts\activate.bat" >nul 2>&1
python "%ROOT%\cli_agent\main.py" %*
