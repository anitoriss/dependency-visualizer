@echo off
rem Stage 2: direct dependencies of a given package version.
chcp 65001 > nul
cd /d "%~dp0.."

call :run -p requests -v 2.31.0
call :run -p requests -v 2.0.0
call :run -p django -v 4.2
call :run -p flask -v 0.10
call :run -p flask
call :run -p six

call :run -p requests -v 99.0
call :run -p no-such-package-xyz
goto :eof

:run
echo.
echo $ depviz %*
call run.bat %*
echo exit code: %errorlevel%
goto :eof
