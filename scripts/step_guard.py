#!/usr/bin/env python3
"""step_guard.py - Atomic micro-step test gate & Two-Hats verifier.

Enforces Martin Fowler's micro-step refactoring loop:
  1. Lock a passing baseline before touching code (`baseline`).
  2. Verify tests stay green and audit Two-Hats separation after each named
     refactoring step (`step`).
  3. Audit current git diff for mixed test + production edits (`check-hats`).
  4. Print an audit log of completed catalog steps (`status`).

Uses Python 3.9+ standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

VERSION = "1.1.0"
DEFAULT_LEDGER = ".refactoring-guard.json"

TEST_FILE_PATTERNS = (
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)__tests__/"),
    re.compile(r"(_test\.py|^test_.*\.py|\.test\.[jt]sx?$|\.spec\.[jt]sx?$|_test\.go$)"),
)


def is_test_path(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    return any(p.search(norm) for p in TEST_FILE_PATTERNS)


def run_shell(cmd: str, cwd: Path) -> Tuple[int, float, str, str]:
    t0 = time.monotonic()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(cmd, shell=True, cwd=str(cwd), env=env, capture_output=True, text=True)
    elapsed = round(time.monotonic() - t0, 3)
    return proc.returncode, elapsed, proc.stdout, proc.stderr


def git_changed_files(cwd: Path) -> List[str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return []
    changed: List[str] = []
    for line in proc.stdout.splitlines():
        if len(line) > 3:
            entry = line[3:].strip()
            if " -> " in entry:
                entry = entry.split(" -> ", 1)[1].strip()
            if not entry.endswith(DEFAULT_LEDGER):
                changed.append(entry)
    return sorted(set(changed))


def git_head(cwd: Path) -> str | None:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(cwd), capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def audit_two_hats(changed: Sequence[str], allow_test_edits: bool) -> Tuple[bool, List[str], List[str]]:
    test_files = [f for f in changed if is_test_path(f)]
    prod_files = [f for f in changed if not is_test_path(f)]
    ok = allow_test_edits or not (test_files and prod_files)
    return ok, prod_files, test_files


def cmd_baseline(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    code, elapsed, out, err = run_shell(args.cmd, cwd)
    if code != 0:
        print(f"FAIL: Baseline test command exited with code {code} ({elapsed}s).", file=sys.stderr)
        if out:
            print(out, file=sys.stderr)
        if err:
            print(err, file=sys.stderr)
        return 1

    digest = hashlib.sha256((out + "\n" + err).encode("utf-8")).hexdigest()[:16]
    ledger_path = cwd / args.ledger
    data: Dict[str, object] = {
        "version": VERSION,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "test_cmd": args.cmd,
        "git_head": git_head(cwd),
        "baseline": {
            "exit_code": code,
            "duration_sec": elapsed,
            "output_hash": digest,
        },
        "steps": [],
    }
    ledger_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: Baseline green in {elapsed}s (output hash {digest}). Ledger written to {ledger_path.name}.")
    return 0


def cmd_step(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    ledger_path = cwd / args.ledger
    ledger: Dict[str, object] = {"steps": []}
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    test_cmd = args.cmd or ledger.get("test_cmd")
    if not test_cmd or not isinstance(test_cmd, str):
        print("ERROR: Provide --cmd or run `baseline` first.", file=sys.stderr)
        return 2

    code, elapsed, out, err = run_shell(test_cmd, cwd)
    if code != 0:
        print(
            f"RED TEST GATE on step '{args.name}' (exit {code}, {elapsed}s).\n"
            "Fowler Ch. 5.1 Rule: Do NOT spend minutes debugging a broken refactoring step.\n"
            "Revert to your last green state immediately (`git checkout -- <files>`) and replay using catalog baby steps!",
            file=sys.stderr,
        )
        if out:
            print(out[-2000:], file=sys.stderr)
        if err:
            print(err[-2000:], file=sys.stderr)
        return 1

    changed = git_changed_files(cwd)
    hats_ok, prod_files, test_files = audit_two_hats(changed, args.allow_test_edits)
    if not hats_ok:
        print(
            "WARNING (Two Hats Check): Both production files and test files have uncommitted edits!\n"
            f"  Production: {', '.join(prod_files)}\n"
            f"  Tests:      {', '.join(test_files)}\n"
            "Under the Refactoring Hat, only adjust tests when migrating a renamed/moved signature "
            "(pass --allow-test-edits when intentional).",
            file=sys.stderr,
        )
        if args.strict_hats:
            return 3

    steps = list(ledger.get("steps", []))  # type: ignore[arg-type]
    entry = {
        "index": len(steps) + 1,
        "name": args.name,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "duration_sec": elapsed,
        "changed_files": changed,
        "two_hats_clean": hats_ok,
    }
    steps.append(entry)
    ledger["steps"] = steps
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(f"PASS [Step {entry['index']}]: {args.name} ({elapsed}s, {len(changed)} files modified)")
    return 0


def cmd_check_hats(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    changed = git_changed_files(cwd)
    ok, prod_files, test_files = audit_two_hats(changed, args.allow_test_edits)
    if ok:
        mode = "production-only" if prod_files else ("test-only" if test_files else "clean working tree")
        print(f"PASS: Two-Hats check clean ({mode}).")
        return 0
    print(
        f"FAIL: Simultaneous production ({len(prod_files)}) and test ({len(test_files)}) edits detected:\n"
        f"  Production: {', '.join(prod_files)}\n"
        f"  Tests:      {', '.join(test_files)}",
        file=sys.stderr,
    )
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    ledger_path = cwd / args.ledger
    if not ledger_path.exists():
        print(f"No ledger found at {ledger_path}. Run `baseline` first.")
        return 0
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    steps = ledger.get("steps", [])
    print(f"# Refactoring Step Ledger ({len(steps)} green steps)\n")
    print(f"- **Test Command**: `{ledger.get('test_cmd')}`")
    base = ledger.get("baseline", {})
    if isinstance(base, dict):
        print(f"- **Baseline**: Green ({base.get('duration_sec')}s, hash `{base.get('output_hash')}`)\n")
    for s in steps:
        print(f"- [x] **Step {s['index']}**: `{s['name']}` ({s['duration_sec']}s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="step_guard.py",
        description="Enforce green baseline, atomic micro-step verification, and Two-Hats separation.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = p.add_subparsers(dest="subcommand", required=True)

    b = sub.add_parser("baseline", help="Verify and record initial passing test baseline")
    b.add_argument("--cmd", required=True, help="Shell test/check command to run")
    b.add_argument("--cwd", default=".", help="Working directory (default: .)")
    b.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"Ledger file name (default: {DEFAULT_LEDGER})")
    b.set_defaults(func=cmd_baseline)

    s = sub.add_parser("step", help="Run test gate and log a named Fowler refactoring micro-step")
    s.add_argument("--name", required=True, help="Canonical refactoring name + target (e.g. '6.1 Extract Function: calcBase')")
    s.add_argument("--cmd", help="Override test command from baseline ledger")
    s.add_argument("--cwd", default=".", help="Working directory (default: .)")
    s.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"Ledger file name (default: {DEFAULT_LEDGER})")
    s.add_argument("--allow-test-edits", action="store_true", help="Permit caller signature updates in test files")
    s.add_argument("--strict-hats", action="store_true", help="Exit non-zero if both prod and test files changed")
    s.set_defaults(func=cmd_step)

    c = sub.add_parser("check-hats", help="Verify git working tree does not mix test and production edits")
    c.add_argument("--cwd", default=".", help="Working directory (default: .)")
    c.add_argument("--allow-test-edits", action="store_true", help="Permit intentional signature migration in tests")
    c.set_defaults(func=cmd_check_hats)

    st = sub.add_parser("status", help="Print Markdown summary of verified refactoring micro-steps")
    st.add_argument("--cwd", default=".", help="Working directory (default: .)")
    st.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"Ledger file name (default: {DEFAULT_LEDGER})")
    st.set_defaults(func=cmd_status)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
