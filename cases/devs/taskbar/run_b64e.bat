@echo off
title Boring - b64e
"%~dp0..\..\..\.venv\Scripts\b64e.exe"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
