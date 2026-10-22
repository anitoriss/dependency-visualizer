@echo off
rem Stage 3: transitive dependency graph (BFS), filter, cycles, test mode.
chcp 65001 > nul
cd /d "%~dp0.."

call :run -p A -t -r examples/repos/simple.txt
call :run -p A -t -r examples/repos/diamond.txt
call :run -p A -t -r examples/repos/cycle.txt
call :run -p A -t -r examples/repos/self_cycle.txt
call :run -p APP -t -r examples/repos/complex.txt
call :run -p APP -t -r examples/repos/complex.txt -f net
call :run -p B -t -r examples/repos/simple.txt

call :run -p A -t -r examples/repos/broken.txt
call :run -p A -t -r examples/repos/bad_name.txt
call :run -p Q -t -r examples/repos/simple.txt
call :run -p APP -t -r examples/repos/complex.txt -f app

call :run -p requests -v 2.31.0
call :run -p flask -f click
goto :eof

:run
echo.
echo $ depviz %*
call run.bat %*
echo exit code: %errorlevel%
goto :eof
