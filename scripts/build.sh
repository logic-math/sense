#!/usr/bin/env bash
# build.sh - Compile sense to bin/sense
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

mkdir -p bin
go build -o bin/sense ./cmd/sense/...

echo "Built: $PROJECT_ROOT/bin/sense"
