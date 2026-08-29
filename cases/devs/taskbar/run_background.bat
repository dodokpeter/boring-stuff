@echo off
title Boring - background
"%~dp0..\..\..\.venv\Scripts\background.exe"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
