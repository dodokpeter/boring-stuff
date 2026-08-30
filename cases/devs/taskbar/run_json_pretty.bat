@echo off
title Boring - json-pretty
"%~dp0..\..\..\.venv\Scripts\json-pretty.exe"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
