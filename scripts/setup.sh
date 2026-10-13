#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$repo_root/.cache/uv}"
export npm_config_cache="${npm_config_cache:-$repo_root/.cache/npm}"
uv venv --allow-existing .venv
uv pip sync --python .venv/bin/python --require-hashes backend/requirements.txt
.venv/bin/python backend/manage.py migrate
cd frontend
npm ci --no-audit --no-fund
