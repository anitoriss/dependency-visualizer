#!/bin/sh
# Stage 2: direct dependencies of a given package version from PyPI.
cd "$(dirname "$0")/.." || exit 1
run() { echo; echo "\$ depviz $*"; ./run.sh "$@"; echo "exit code: $?"; }

run -p requests -v 2.31.0
run -p requests -v 2.0.0
run -p django -v 4.2
run -p flask -v 0.10
run -p flask
run -p six

run -p requests -v 99.0
run -p no-such-package-xyz
