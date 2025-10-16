#!/usr/bin/env bash
set -euo pipefail

python_backend_output=$(python sample_project/backend/service.py)
node_frontend_output="npm run build" # placeholder for bundler invocation

echo "Python backend summary:\n${python_backend_output}"
echo "Frontend build command: ${node_frontend_output}"
