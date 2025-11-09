#!/usr/bin/env bash
set -euo pipefail
echo "[start.sh] Python: $(python -V)"
echo "[start.sh] TZ: ${TZ:-UTC}"
python -m src.fix_schema || true
exec python -m src.run_loop
