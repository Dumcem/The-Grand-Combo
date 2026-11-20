"""Write a read-only inventory of explicitly selected runtime paths to stdout."""

import argparse
import json
from pathlib import Path
import sys

from deploy_tgc import DeploymentError, no_links, snapshot


def capture(roots):
    paths = {}
    for label, value in roots:
        if label in paths:
            raise ValueError(f"Duplicate path label: {label}")
        path = Path(value)
        if not path.is_absolute():
            raise ValueError(f"An absolute path is required for {label}")
        path = no_links(path).resolve()
        paths[label] = {"path": str(path), "contents": snapshot(path)}
    return {"schema": 1, "paths": paths}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", nargs=2, metavar=("LABEL", "ABSOLUTE_PATH"),
                        action="append", required=True)
    args = parser.parse_args(argv)
    try:
        result = capture(args.path)
    except (DeploymentError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
