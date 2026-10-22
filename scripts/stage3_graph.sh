#!/bin/sh
# Stage 3: transitive dependency graph (BFS), filter, cycles, test mode.
cd "$(dirname "$0")/.." || exit 1
run() { echo; echo "\$ depviz $*"; ./run.sh "$@"; echo "exit code: $?"; }
R=examples/repos

run -p A -t -r $R/simple.txt
run -p A -t -r $R/diamond.txt
run -p A -t -r $R/cycle.txt
run -p A -t -r $R/self_cycle.txt
run -p APP -t -r $R/complex.txt
run -p APP -t -r $R/complex.txt -f net
run -p B -t -r $R/simple.txt

run -p A -t -r $R/broken.txt
run -p A -t -r $R/bad_name.txt
run -p Q -t -r $R/simple.txt
run -p APP -t -r $R/complex.txt -f app

run -p requests -v 2.31.0
run -p flask -f click
