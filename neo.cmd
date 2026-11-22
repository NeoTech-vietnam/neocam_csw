@echo off
python "%~dp0TOOLCONF\dev.py" %*
exit /b %errorlevel%
