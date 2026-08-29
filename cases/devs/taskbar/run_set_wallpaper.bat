@echo off
title Boring - set-wallpaper
"%~dp0..\..\..\.venv\Scripts\set-wallpaper.exe"
echo.
echo Closing in 60 seconds...
ping -n 61 127.0.0.1 >nul
