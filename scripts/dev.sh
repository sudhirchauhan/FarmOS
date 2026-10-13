#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
api_pid=""
web_pid=""
cleanup() {
    for pid in "$api_pid" "$web_pid"; do
        if [ -n "$pid" ]; then kill "$pid" 2>/dev/null || true; fi
    done
    wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
.venv/bin/python backend/manage.py runserver 127.0.0.1:8000 --noreload &
api_pid=$!
cd frontend
node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 &
web_pid=$!
wait -n "$api_pid" "$web_pid"
