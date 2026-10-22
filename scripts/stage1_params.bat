@echo off
rem Stage 1: all parameters and error handling for every parameter.
chcp 65001 > nul
cd /d "%~dp0.."

call :run --package requests
call :run -p flask -r https://pypi.org/pypi -v 3.0.0 -o out.svg -a -f click
call :run -p A -t -r examples/repos/simple.txt

call :run
call :run -p "bad name!"
call :run -p requests -r ftp://example.org
call :run -p requests -v abc
call :run -p requests -o graph.png
call :run -p requests -o no/such/dir/graph.svg
call :run -p requests -f ""
call :run -p A -t
call :run -p A -t -r missing.txt
call :run -p requests -t -r examples/repos/simple.txt
call :run -p A -t -r examples/repos/simple.txt -v 1.0
goto :eof

:run
echo.
echo $ depviz %*
call run.bat %*
echo exit code: %errorlevel%
goto :eof
