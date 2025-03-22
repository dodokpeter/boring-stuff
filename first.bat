@ECHO OFF
ECHO *********************************************************
ECHO Let's start with boring stuff in your windows machine
ECHO Welcome and enjoy automation
ECHO *********************************************************
ECHO Adding scripts to the path..
@ECHO ON

SETX BORING_STUFF_PATH "%CD%"

REM Append user path
SET Key="HKCU\Environment"
FOR /F "usebackq tokens=2*" %%A IN (`REG QUERY %Key% /v PATH`) DO SET CurrPath=%%B

REM Display current PATH
ECHO Curren path
ECHO %CurrPath%

REM Set permanently path to scripts into user environment variable
SETX PATH "%CurrPath%;%BORING_STUFF_PATH%\scripts\"

ECHO *********************************************************
ECHO %PATH%
ECHO *********************************************************



REM Check if PYTHONPATH already exists
SET KEY="HKCU\Environment"
FOR /F "usebackq tokens=2*" %%A IN (`REG QUERY %KEY% /v PYTHONPATH`) DO SET EXISTING_PYTHONPATH=%%B

REM If PYTHONPATH already exists, append the new value
IF DEFINED EXISTING_PYTHONPATH (
    SET NEW_PYTHONPATH=%EXISTING_PYTHONPATH%;%BORING_STUFF_PATH%
) ELSE (
    SET NEW_PYTHONPATH=%BORING_STUFF_PATH%
)

REM Set PYTHONPATH permanently
SETX PYTHONPATH "%NEW_PYTHONPATH%"

REM Check Python version by running the version.py script
ECHO Checking Python...
FOR /f "usebackq tokens=*" %%A IN (`python %BORING_STUFF_PATH%\python\version.py %*`) DO SET PYTHON_VERSION=%%A

ECHO %PYTHON_VERSION%



ECHO Creating new configuration..

REM Use USERPROFILE instead of HOME for a reliable home directory
SET HOME_DIR=%USERPROFILE%\boring-stuff

REM Delete existing directory safely
IF EXIST "%HOME_DIR%" RMDIR /s /q "%HOME_DIR%"

REM Create the directory
MKDIR "%HOME_DIR%"

REM Copy the configuration file, forcing overwrite
COPY /Y "BoringStuff.yml" "%HOME_DIR%\BoringStuff.yml"

ECHO Configuration copied successfully!

ECHO End initialisation process, thanks