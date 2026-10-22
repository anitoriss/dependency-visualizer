#!/bin/sh
# Usage: ./run.sh [options]
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$DIR/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m depviz "$@"
