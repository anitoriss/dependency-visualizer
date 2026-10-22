#!/bin/sh
# Stage 1: all parameters and error handling for every parameter.
cd "$(dirname "$0")/.." || exit 1
run() { echo; echo "\$ depviz $*"; ./run.sh "$@"; echo "exit code: $?"; }

run --package requests
run -p flask -r https://pypi.org/pypi -v 3.0.0 -o out.svg -a -f click
run -p A -t -r examples/repos/simple.txt

run
run -p "bad name!"
run -p requests -r ftp://example.org
run -p requests -v abc
run -p requests -o graph.png
run -p requests -o no/such/dir/graph.svg
run -p requests -f ""
run -p A -t
run -p A -t -r missing.txt
run -p requests -t -r examples/repos/simple.txt
run -p A -t -r examples/repos/simple.txt -v 1.0
