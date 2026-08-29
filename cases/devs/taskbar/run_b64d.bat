@echo off
title Boring - b64d
"%~dp0..\..\..\.venv\Scripts\b64d.exe"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
