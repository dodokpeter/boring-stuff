@echo off
title Boring - mp4to3
"%~dp0..\..\..\.venv\Scripts\mp4to3.exe" "%~1"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
