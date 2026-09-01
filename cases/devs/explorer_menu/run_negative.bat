@echo off
title Boring - negative
"%~dp0..\..\..\.venv\Scripts\negative.exe" "%~1"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
