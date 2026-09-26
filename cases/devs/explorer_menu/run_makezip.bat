@echo off
title Boring - makezip
"%~dp0..\..\..\.venv\Scripts\makezip.exe" "%~1"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
