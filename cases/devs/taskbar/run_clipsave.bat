@echo off
title Boring - clipsave
"%~dp0..\..\..\.venv\Scripts\clipsave.exe"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
