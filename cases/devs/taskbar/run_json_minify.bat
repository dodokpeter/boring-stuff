@echo off
title Boring - json-pretty -m
"%~dp0..\..\..\.venv\Scripts\json-pretty.exe" -m
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
