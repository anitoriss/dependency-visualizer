@echo off
rem Usage: run.bat [options]
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
python -m depviz %*
