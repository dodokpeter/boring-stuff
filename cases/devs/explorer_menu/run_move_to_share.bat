@echo off
title Boring - move-to -s
"%~dp0..\..\..\.venv\Scripts\move-to.exe" -s "%~1"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
