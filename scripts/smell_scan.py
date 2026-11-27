#!/usr/bin/env python3
"""smell_scan.py - Zero-dependency structural code smell scanner (Fowler 2nd Ed.).

Scans Python files via `ast` and JS/TS/Go/Java/C#/Rust files via lightweight
structural heuristics, reporting file:line coordinates and recommended Fowler
refactorings. Uses Python 3.9+ standard library only.
"""

from __future__ import annotations

import argparse
import ast
import collections
import itertools
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

VERSION = "1.1.0"

SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "out",
    ".next",
    "__pycache__",
    ".venv",
    "venv",
    "vendor",
    "coverage",
    "target",
}

PY_EXTS = {".py"}
BRACE_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".java", ".cs", ".rs", ".kt"}


@dataclass
class Finding:
    file: str
    line: int
    smell: str
    symbol: str
    detail: str
    refactorings: List[str]


def iter_source_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in sorted(dirs) if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in sorted(files):
            p = Path(root) / fname
            if p.suffix.lower() in (PY_EXTS | BRACE_EXTS):
                yield p


def _max_py_branch_depth(node: ast.AST, depth: int = 0) -> int:
    branch_types = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try)
    if hasattr(ast, "Match"):
        branch_types = branch_types + (getattr(ast, "Match"),)
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        is_elif = isinstance(node, ast.If) and child in getattr(node, "orelse", []) and isinstance(child, ast.If)
        next_depth = depth if is_elif else (depth + 1 if isinstance(child, branch_types) else depth)
        best = max(best, _max_py_branch_depth(child, next_depth))
    return best


def _extract_py_switch_key(node: ast.If) -> str | None:
    if len(node.orelse) != 1 or not isinstance(node.orelse[0], ast.If):
        return None
    if isinstance(node.test, ast.Compare) and len(node.test.ops) == 1 and isinstance(node.test.ops[0], (ast.Eq, ast.In)):
        return ast.unparse(node.test.left) if hasattr(ast, "unparse") else None
    return None


def _detect_py_temporary_fields(cls_node: ast.ClassDef, rel_path: str) -> List[Finding]:
    methods = [n for n in cls_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(methods) < 3:
        return []

    nullable_init_fields: dict[str, int] = {}
    non_none_writers: dict[str, Set[str]] = collections.defaultdict(set)

    for m in methods:
        for sub in ast.walk(m):
            targets: List[Tuple[ast.AST, ast.AST | None, int]] = []
            if isinstance(sub, ast.Assign):
                for t in sub.targets:
                    targets.append((t, sub.value, sub.lineno))
            elif isinstance(sub, ast.AnnAssign) and sub.value is not None:
                targets.append((sub.target, sub.value, sub.lineno))

            for t, val, lineno in targets:
                if (
                    isinstance(t, ast.Attribute)
                    and isinstance(t.value, ast.Name)
                    and t.value.id == "self"
                ):
                    is_none = isinstance(val, ast.Constant) and val.value is None
                    if m.name == "__init__" and is_none:
                        nullable_init_fields[t.attr] = lineno
                    elif m.name != "__init__" and not is_none:
                        non_none_writers[t.attr].add(m.name)

    results: List[Finding] = []
    for attr, lineno in sorted(nullable_init_fields.items()):
        writers = non_none_writers.get(attr, set())
        if len(writers) == 1:
            writer_name = next(iter(writers))
            results.append(
                Finding(
                    file=rel_path,
                    line=lineno,
                    smell="Temporary Field",
                    symbol=f"{cls_node.name}.{attr}",
                    detail=(
                        f"Field 'self.{attr}' starts as None in __init__ and is populated only inside '{writer_name}'"
                    ),
                    refactorings=[
                        "7.5 Extract Class",
                        "11.9 Replace Function with Command",
                        "10.5 Introduce Special Case",
                    ],
                )
            )
    return results


def scan_python_file(
    path: Path,
    rel_path: str,
    max_fn_lines: int,
    max_params: int,
    max_nesting: int,
    max_class_methods: int,
    param_tuples: dict[Tuple[str, ...], List[Tuple[str, int, str]]],
    switch_keys: dict[str, List[Tuple[str, int, str]]],
) -> List[Finding]:
    findings: List[Finding] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return findings

    src_lines = source.splitlines()

    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and not target.id.isupper() and not target.id.startswith("_"):
                    if isinstance(stmt.value, (ast.Dict, ast.List, ast.Set, ast.Call)):
                        findings.append(
                            Finding(
                                file=rel_path,
                                line=stmt.lineno,
                                smell="Global / Mutable Module Data",
                                symbol=target.id,
                                detail=f"Mutable module-level binding '{target.id}' exposed without accessors",
                                refactorings=["6.6 Encapsulate Variable", "7.1 Encapsulate Record"],
                            )
                        )

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if len(methods) > max_class_methods:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=node.lineno,
                        smell="Large Class",
                        symbol=node.name,
                        detail=f"Class '{node.name}' defines {len(methods)} methods (threshold: {max_class_methods})",
                        refactorings=["6.1 Extract Function", "7.5 Extract Class", "12.8 Extract Superclass"],
                    )
                )
            findings.extend(_detect_py_temporary_fields(node, rel_path))

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            span = end_line - node.lineno + 1
            if span > max_fn_lines:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=node.lineno,
                        smell="Long Function",
                        symbol=node.name,
                        detail=f"Function '{node.name}' spans {span} lines (threshold: {max_fn_lines})",
                        refactorings=[
                            "6.1 Extract Function",
                            "7.4 Replace Temp with Query",
                            "6.11 Split Phase",
                        ],
                    )
                )

            fn_slice = src_lines[node.lineno - 1 : end_line]
            comment_count = sum(1 for ln in fn_slice if ln.lstrip().startswith("#"))
            if span >= 20 and comment_count >= 6:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=node.lineno,
                        smell="Comments (Potential Deodorant)",
                        symbol=node.name,
                        detail=f"Function '{node.name}' embeds {comment_count} inline comment lines; check if blocks can be extracted",
                        refactorings=[
                            "6.1 Extract Function",
                            "6.5 Change Function Declaration",
                            "10.6 Introduce Assertion",
                        ],
                    )
                )

            raw_args = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
            params = [p for p in raw_args if p not in ("self", "cls")]
            if len(params) > max_params:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=node.lineno,
                        smell="Long Parameter List",
                        symbol=node.name,
                        detail=f"Function '{node.name}' takes {len(params)} parameters ({', '.join(params)})",
                        refactorings=[
                            "6.8 Introduce Parameter Object",
                            "11.4 Preserve Whole Object",
                            "11.5 Replace Parameter with Query",
                        ],
                    )
                )

            if len(params) >= 3:
                for combo in itertools.combinations(sorted(set(params))[:8], 3):
                    param_tuples[combo].append((rel_path, node.lineno, node.name))

            defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
            for d in defaults:
                if isinstance(d, ast.Constant) and isinstance(d.value, bool):
                    findings.append(
                        Finding(
                            file=rel_path,
                            line=node.lineno,
                            smell="Flag Argument",
                            symbol=node.name,
                            detail=f"Function '{node.name}' has boolean default parameter switching behavior",
                            refactorings=["11.3 Remove Flag Argument", "10.1 Decompose Conditional"],
                        )
                    )
                    break

            depth = _max_py_branch_depth(node)
            if depth > max_nesting:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=node.lineno,
                        smell="Deep Conditional / Loop Nesting",
                        symbol=node.name,
                        detail=f"Function '{node.name}' reaches control-flow nesting depth {depth} (threshold: {max_nesting})",
                        refactorings=[
                            "10.3 Replace Nested Conditional with Guard Clauses",
                            "10.1 Decompose Conditional",
                            "6.1 Extract Function",
                        ],
                    )
                )

            for sub in ast.walk(node):
                if isinstance(sub, ast.If):
                    key = _extract_py_switch_key(sub)
                    if key:
                        switch_keys[key].append((rel_path, sub.lineno, node.name))
                if hasattr(ast, "Match") and isinstance(sub, getattr(ast, "Match")):
                    subj = ast.unparse(sub.subject) if hasattr(ast, "unparse") else "match"
                    switch_keys[subj].append((rel_path, sub.lineno, node.name))

    for idx, line in enumerate(src_lines, 1):
        code_part = line.split("#", 1)[0]
        m = re.search(r"\b([A-Za-z_]\w*(?:\.[A-Za-z_]\w*\s*(?:\([^()]*\))?){3,})", code_part)
        if m and not code_part.lstrip().startswith(("import ", "from ")):
            chain = m.group(1)
            if not any(pkg in chain for pkg in ("os.path.", "sys.", "logging.", "urllib.")):
                findings.append(
                    Finding(
                        file=rel_path,
                        line=idx,
                        smell="Message Chains",
                        symbol=chain[:48],
                        detail=f"Deep navigation chain '{chain[:60]}' couples caller to intermediate structure",
                        refactorings=["7.7 Hide Delegate", "6.1 Extract Function", "8.1 Move Function"],
                    )
                )

    return findings


FN_DECL_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:public|private|protected|internal|static|async|fn|func|function)\b"
    r"[^{;=]*?\b([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*(?::[^{;=]+)?\{"
)
ARROW_FN_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?::[^=]+)?=>\s*\{"
)
SWITCH_RE = re.compile(r"\bswitch\s*\(([^)]+)\)")
MUTABLE_GLOBAL_JS_RE = re.compile(r"^(?:export\s+)?(?:let|var)\s+([A-Za-z_$][\w$]*)\s*=")


def scan_brace_file(
    path: Path,
    rel_path: str,
    max_fn_lines: int,
    max_params: int,
    max_nesting: int,
    param_tuples: dict[Tuple[str, ...], List[Tuple[str, int, str]]],
    switch_keys: dict[str, List[Tuple[str, int, str]]],
) -> List[Finding]:
    findings: List[Finding] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    n = len(lines)
    brace_depth = 0

    for i, raw in enumerate(lines):
        lineno = i + 1
        stripped = re.sub(r"//.*$", "", raw)

        if brace_depth == 0 and path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            gm = MUTABLE_GLOBAL_JS_RE.match(stripped)
            if gm:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=lineno,
                        smell="Global / Mutable Module Data",
                        symbol=gm.group(1),
                        detail=f"Top-level mutable '{gm.group(1)}' variable can be mutated across functions",
                        refactorings=["6.6 Encapsulate Variable", "9.1 Split Variable"],
                    )
                )

        m = FN_DECL_RE.match(stripped) or ARROW_FN_RE.match(stripped)
        if m and m.group(1) not in {"if", "for", "while", "switch", "catch"}:
            fn_name = m.group(1)
            raw_params = [p.strip() for p in m.group(2).split(",") if p.strip()]
            clean_params = []
            has_bool_flag = False
            for p in raw_params:
                if re.search(r"=\s*(true|false)\b|:\s*boolean\b", p):
                    has_bool_flag = True
                pname = re.split(r"[:=]", p)[0].strip().split()[-1].lstrip("*&.")
                if pname and pname not in {"this", "self"}:
                    clean_params.append(pname)

            if len(clean_params) > max_params:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=lineno,
                        smell="Long Parameter List",
                        symbol=fn_name,
                        detail=f"Function '{fn_name}' takes {len(clean_params)} parameters",
                        refactorings=[
                            "6.8 Introduce Parameter Object",
                            "11.4 Preserve Whole Object",
                            "11.5 Replace Parameter with Query",
                        ],
                    )
                )
            if len(clean_params) >= 3:
                for combo in itertools.combinations(sorted(set(clean_params))[:8], 3):
                    param_tuples[combo].append((rel_path, lineno, fn_name))
            if has_bool_flag:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=lineno,
                        smell="Flag Argument",
                        symbol=fn_name,
                        detail=f"Function '{fn_name}' declares a boolean parameter or default literal",
                        refactorings=["11.3 Remove Flag Argument", "10.1 Decompose Conditional"],
                    )
                )

            local_depth = 0
            max_local_ctrl = 0
            end_idx = i
            for j in range(i, n):
                seg = re.sub(r"//.*$", "", lines[j])
                opens = seg.count("{")
                closes = seg.count("}")
                if j > i and re.search(r"\b(if|for|while|switch)\s*\(", seg):
                    max_local_ctrl = max(max_local_ctrl, local_depth)
                local_depth += opens - closes
                sm = SWITCH_RE.search(seg)
                if sm:
                    switch_keys[sm.group(1).strip()].append((rel_path, j + 1, fn_name))
                if local_depth <= 0 and j >= i:
                    end_idx = j
                    break
            span = end_idx - i + 1
            if span > max_fn_lines:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=lineno,
                        smell="Long Function",
                        symbol=fn_name,
                        detail=f"Function '{fn_name}' spans {span} lines (threshold: {max_fn_lines})",
                        refactorings=[
                            "6.1 Extract Function",
                            "7.4 Replace Temp with Query",
                            "6.11 Split Phase",
                        ],
                    )
                )
            if max_local_ctrl > max_nesting:
                findings.append(
                    Finding(
                        file=rel_path,
                        line=lineno,
                        smell="Deep Conditional / Loop Nesting",
                        symbol=fn_name,
                        detail=f"Function '{fn_name}' reaches block nesting depth {max_local_ctrl} (threshold: {max_nesting})",
                        refactorings=[
                            "10.3 Replace Nested Conditional with Guard Clauses",
                            "10.1 Decompose Conditional",
                        ],
                    )
                )

        brace_depth = max(0, brace_depth + stripped.count("{") - stripped.count("}"))

    return findings


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="smell_scan.py",
        description="Scan source files for structural Fowler (2nd Ed.) code smells and output recommended refactorings.",
    )
    p.add_argument("target", help="File or directory path to scan")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    p.add_argument("--json", action="store_true", help="Emit JSON array instead of Markdown report")
    p.add_argument("--max-fn-lines", type=int, default=40, help="Line threshold for Long Function (default: 40)")
    p.add_argument("--max-params", type=int, default=4, help="Parameter threshold for Long Parameter List (default: 4)")
    p.add_argument("--max-nesting", type=int, default=3, help="Max control-flow nesting depth (default: 3)")
    p.add_argument("--max-class-methods", type=int, default=15, help="Method count threshold for Large Class (default: 15)")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target = Path(args.target).resolve()
    if not target.exists():
        print(f"ERROR: Target path does not exist: {args.target}", file=sys.stderr)
        return 2

    base = target.parent if target.is_file() else target
    findings: List[Finding] = []
    param_tuples: dict[Tuple[str, ...], List[Tuple[str, int, str]]] = collections.defaultdict(list)
    switch_keys: dict[str, List[Tuple[str, int, str]]] = collections.defaultdict(list)

    for file_path in iter_source_files(target):
        rel = str(file_path.relative_to(base))
        if file_path.suffix.lower() in PY_EXTS:
            findings.extend(
                scan_python_file(
                    file_path,
                    rel,
                    args.max_fn_lines,
                    args.max_params,
                    args.max_nesting,
                    args.max_class_methods,
                    param_tuples,
                    switch_keys,
                )
            )
        else:
            findings.extend(
                scan_brace_file(
                    file_path,
                    rel,
                    args.max_fn_lines,
                    args.max_params,
                    args.max_nesting,
                    param_tuples,
                    switch_keys,
                )
            )

    # Deduplicate overlapping 3-param Data Clumps sharing identical function site-sets
    merged_clumps: dict[Tuple[Tuple[str, int, str], ...], Set[str]] = collections.defaultdict(set)
    for params, sites in param_tuples.items():
        unique_sites = tuple(dict.fromkeys(sites))
        if len(unique_sites) >= 2:
            merged_clumps[unique_sites].update(params)

    for unique_sites, param_set in sorted(merged_clumps.items()):
        ordered_params = sorted(param_set)
        locs = ", ".join(f"{f}:{ln} ({fn})" for f, ln, fn in unique_sites[:4])
        f0, ln0, fn0 = unique_sites[0]
        findings.append(
            Finding(
                file=f0,
                line=ln0,
                smell="Data Clumps",
                symbol=fn0,
                detail=f"Parameter group ({', '.join(ordered_params)}) repeats across {len(unique_sites)} functions: {locs}",
                refactorings=["6.8 Introduce Parameter Object", "7.5 Extract Class", "11.4 Preserve Whole Object"],
            )
        )

    # Cross-function Repeated Switches
    for key, sites in sorted(switch_keys.items()):
        unique_sites = list(dict.fromkeys(sites))
        if len(unique_sites) >= 2:
            locs = ", ".join(f"{f}:{ln} ({fn})" for f, ln, fn in unique_sites[:4])
            f0, ln0, fn0 = unique_sites[0]
            findings.append(
                Finding(
                    file=f0,
                    line=ln0,
                    smell="Repeated Switches",
                    symbol=key,
                    detail=f"Discriminator '{key}' switches across {len(unique_sites)} places: {locs}",
                    refactorings=[
                        "10.4 Replace Conditional with Polymorphism",
                        "12.6 Replace Type Code with Subclasses",
                        "12.10 Replace Subclass with Delegate",
                    ],
                )
            )

    findings.sort(key=lambda x: (x.file, x.line, x.smell))

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
        return 0

    if not findings:
        print("No structural code smells exceeded thresholds.")
        return 0

    print(f"# Structural Smell Triage ({len(findings)} findings)\n")
    print("| Location | Smell | Symbol | Detail | Recommended Fowler Refactorings |")
    print("| --- | --- | --- | --- | --- |")
    for f in findings:
        refs = ", ".join(f"`{r}`" for r in f.refactorings)
        print(f"| `{f.file}:{f.line}` | **{f.smell}** | `{f.symbol}` | {f.detail} | {refs} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
