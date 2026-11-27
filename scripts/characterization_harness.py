#!/usr/bin/env python3
"""characterization_harness.py - Golden-master snapshot runner for legacy seams.

Implements Fowler Ch. 4 & Feathers's characterization testing workflow when a
legacy module lacks unit tests:
  1. `init-template`: Generate a starter `cases.json` boundary input manifest.
  2. `record`: Execute each seam command across normal & boundary inputs and
     save exact exit codes, stdout, stderr, and hashes.
  3. `verify`: Re-execute all cases after each refactoring step and fail with a
     unified diff if observable output drifts by a single character.

Uses Python 3.9+ standard library only.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence

VERSION = "1.1.0"

SAMPLE_MANIFEST = {
    "cases": [
        {
            "id": "happy-path",
            "cmd": ["python3", "legacy_billing.py", "--customer", "acme"],
            "stdin": "",
            "env": {},
        },
        {
            "id": "empty-orders-boundary",
            "cmd": ["python3", "legacy_billing.py", "--customer", "empty"],
            "stdin": "",
            "env": {},
        },
        {
            "id": "zero-and-threshold-boundary",
            "cmd": ["python3", "legacy_billing.py", "--customer", "threshold-500"],
            "stdin": "",
            "env": {},
        },
    ]
}


def run_case(case: Dict[str, object], cwd: Path) -> Dict[str, object]:
    cmd = case["cmd"]
    stdin_text = str(case.get("stdin", ""))
    extra_env = case.get("env", {}) or {}
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **{str(k): str(v) for k, v in dict(extra_env).items()}}  # type: ignore[arg-type]

    if isinstance(cmd, list):
        proc = subprocess.run([str(x) for x in cmd], input=stdin_text, cwd=str(cwd), env=env, capture_output=True, text=True)
    else:
        proc = subprocess.run(str(cmd), shell=True, input=stdin_text, cwd=str(cwd), env=env, capture_output=True, text=True)

    payload = f"EXIT:{proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return {
        "id": str(case["id"]),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "sha256": digest,
    }


def cmd_init_template(args: argparse.Namespace) -> int:
    out_path = Path(args.out)
    if out_path.exists() and not args.force:
        print(f"ERROR: {out_path} already exists (pass --force to overwrite).", file=sys.stderr)
        return 2
    out_path.write_text(json.dumps(SAMPLE_MANIFEST, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote sample characterization manifest to {out_path}")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cases: List[Dict[str, object]] = manifest.get("cases", [])
    if not cases:
        print("ERROR: Manifest contains zero cases.", file=sys.stderr)
        return 2

    recorded = [run_case(c, cwd) for c in cases]
    snap_path = Path(args.snapshots)
    snap_path.write_text(json.dumps({"version": VERSION, "results": recorded}, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: Recorded {len(recorded)} characterization snapshots to {snap_path}.")
    print("Tip: Mutate one operator in target code and run `verify` now to confirm fault injection turns red!")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    snap_data = json.loads(Path(args.snapshots).read_text(encoding="utf-8"))
    expected_map = {r["id"]: r for r in snap_data.get("results", [])}

    failures = 0
    for case in manifest.get("cases", []):
        cid = str(case["id"])
        if cid not in expected_map:
            print(f"FAIL [{cid}]: Missing baseline snapshot entry.", file=sys.stderr)
            failures += 1
            continue
        exp = expected_map[cid]
        act = run_case(case, cwd)
        if exp["sha256"] != act["sha256"]:
            failures += 1
            print(f"FAIL [{cid}]: Observable behavior drifted!", file=sys.stderr)
            if exp["exit_code"] != act["exit_code"]:
                print(f"  exit_code: expected {exp['exit_code']}, got {act['exit_code']}", file=sys.stderr)
            if exp["stdout"] != act["stdout"]:
                diff = difflib.unified_diff(
                    str(exp["stdout"]).splitlines(keepends=True),
                    str(act["stdout"]).splitlines(keepends=True),
                    fromfile=f"{cid}:baseline.stdout",
                    tofile=f"{cid}:current.stdout",
                )
                sys.stderr.writelines(diff)
            if exp["stderr"] != act["stderr"]:
                diff = difflib.unified_diff(
                    str(exp["stderr"]).splitlines(keepends=True),
                    str(act["stderr"]).splitlines(keepends=True),
                    fromfile=f"{cid}:baseline.stderr",
                    tofile=f"{cid}:current.stderr",
                )
                sys.stderr.writelines(diff)

    if failures:
        print(f"\nVERIFY FAILED: {failures} case(s) drifted from golden master.", file=sys.stderr)
        return 1
    print(f"PASS: All {len(manifest.get('cases', []))} characterization cases match golden master byte-for-byte.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="characterization_harness.py",
        description="Capture and verify golden-master characterization snapshots on untested legacy seams.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = p.add_subparsers(dest="subcommand", required=True)

    it = sub.add_parser("init-template", help="Write starter cases.json manifest")
    it.add_argument("--out", default="cases.json", help="Output path (default: cases.json)")
    it.add_argument("--force", action="store_true", help="Overwrite existing file")
    it.set_defaults(func=cmd_init_template)

    rc = sub.add_parser("record", help="Record golden-master outputs for all cases")
    rc.add_argument("--manifest", required=True, help="Path to cases.json")
    rc.add_argument("--snapshots", default="snapshots.json", help="Output snapshot file (default: snapshots.json)")
    rc.add_argument("--cwd", default=".", help="Working directory (default: .)")
    rc.set_defaults(func=cmd_record)

    vf = sub.add_parser("verify", help="Verify current outputs match recorded snapshots byte-for-byte")
    vf.add_argument("--manifest", required=True, help="Path to cases.json")
    vf.add_argument("--snapshots", default="snapshots.json", help="Snapshot file to compare against")
    vf.add_argument("--cwd", default=".", help="Working directory (default: .)")
    vf.set_defaults(func=cmd_verify)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
