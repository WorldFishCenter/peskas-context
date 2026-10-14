"""Copy the brand files into the Peskas repos, or check that their copies match.

    python sync.py                 # every repo listed in consumers.json
    python sync.py peskas.show     # some repos only
    python sync.py --check         # report copies that differ or are missing; exit 1 if any do
    python sync.py --dir peskas.coasts=../peskas.coasts-logo   # a repo checked out elsewhere

Repos are found next to this peskas-context checkout (its parent folder). Standard library only.
"""

import argparse
import filecmp
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "consumers.json").read_text())


def pairs(repo):
    """[(file in brand/, path in the repo)] for one repo."""
    spec = CONFIG["repos"][repo]
    if "r_package" in spec:
        return [(src.format(name=spec["r_package"]), dst) for src, dst in CONFIG["r_package_files"]]
    return [tuple(p) for p in spec["files"]]


def sync(repo, root, check):
    """Copy (or compare) one repo's files; return the paths that were out of date."""
    stale = []
    for src, dst in pairs(repo):
        source, target = HERE / src, root / dst
        if not source.is_file():
            raise FileNotFoundError(f"brand/{src} is missing: run build.py")
        if target.is_file() and filecmp.cmp(source, target, shallow=False):
            continue
        stale.append(dst)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return stale


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos", nargs="*", help="repo folder names (default: all in consumers.json)")
    ap.add_argument("--check", action="store_true", help="only report copies that differ or are missing")
    ap.add_argument("--dir", action="append", default=[], metavar="REPO=PATH", help="where a repo is checked out, if not next to peskas-context")
    args = ap.parse_args(argv)
    names = args.repos or list(CONFIG["repos"])
    unknown = [n for n in names if n not in CONFIG["repos"]]
    if unknown:
        ap.error(f"not in consumers.json: {', '.join(unknown)}")
    dirs = dict(d.split("=", 1) for d in args.dir)
    base = HERE.parent.parent
    drift = False
    for name in names:
        root = Path(dirs.get(name, base / name)).resolve()
        if not root.is_dir():
            print(f"{name}: not found at {root}, skipped")
            continue
        stale = sync(name, root, args.check)
        if not stale:
            print(f"{name}: up to date")
            continue
        drift = True
        verb = "differs" if args.check else "updated"
        print(f"{name}: {len(stale)} {verb}")
        for path in stale:
            print(f"  {path}")
        note = CONFIG["repos"][name].get("after")
        if note and not args.check:
            print(f"  then: {note}")
    return 1 if (drift and args.check) else 0


def _self_test():
    """Copy into a temporary repo, then check: the second pass finds nothing stale."""
    import tempfile
    name = "peskas-api"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = sync(name, root, check=False)
        assert first == [dst for _, dst in pairs(name)], first
        assert sync(name, root, check=True) == []
        (root / pairs(name)[0][1]).write_text("changed")
        assert sync(name, root, check=True) == [pairs(name)[0][1]]
    print("self-test ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        _self_test()
    else:
        sys.exit(main())
