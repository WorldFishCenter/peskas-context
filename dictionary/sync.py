"""Copy the generated files into the Peskas repos, or check that their copies match.

    python sync.py                 # every repo listed in consumers.json
    python sync.py --check         # report copies that differ or are missing; exit 1 if any do

The same as brand/sync.py (and its options), with this folder's consumers.json.
"""

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("brand_sync", HERE.parent / "brand" / "sync.py")
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
kit.HERE, kit.CONFIG = HERE, json.loads((HERE / "consumers.json").read_text())

if __name__ == "__main__":
    sys.exit(kit.main())
