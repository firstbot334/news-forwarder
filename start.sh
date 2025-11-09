#!/usr/bin/env bash
set -euo pipefail

echo "[start.sh] Python: $(python -V)"
echo "[start.sh] CWD: $(pwd)"
echo "[start.sh] Listing:"
ls -al

# Normalize line endings just in case this file was edited on Windows
if command -v dos2unix >/dev/null 2>&1; then
  dos2unix -q start.sh || true
fi

run_py() {
  echo "[start.sh] running: $*"
  exec python - <<'PYCODE'
import importlib, logging, sys
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def have(mod):
    try:
        import importlib.util
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False

# Try src.* layout
if have("src.fix_schema") and have("src.run_loop"):
    import src.fix_schema  # schema ensure
    from src.run_loop import main
    main()
# Try app.* layout
elif have("fix_schema") and have("run_loop"):
    import fix_schema  # schema ensure
    from run_loop import main
    main()
# Try app.main shim
elif have("app.main"):
    import app.main  # will run if it's written as __main__
else:
    print("FATAL: cannot find (src.fix_schema & src.run_loop) nor (fix_schema & run_loop) nor app.main", file=sys.stderr)
    sys.exit(1)
PYCODE
}

run_py
