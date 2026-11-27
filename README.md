# Refactoring Skill (Fowler 2nd Edition, v1.1.0)

An agent-agnostic skill distilling all 12 chapters and Preface of Martin Fowler's *Refactoring: Improving the Design of Existing Code (2nd Edition)* into behavior-preserving workflows, a master cheat sheet and diagnostic matrix for all **24 Bad Smells in Code**, a **61-item Master Catalog Index** (with 1st-edition alias mappings and inverse moves), step-by-step mechanics with worked variants and Before/After sketches for all **61 Canonical Refactorings**, **7 multi-stage architectural playbooks**, copyable runbook templates, and zero-dependency Python 3 verification scripts.

## Directory Layout

```text
refactoring/
├── SKILL.md                                     # Core agent instructions, 6 invariants, decision trees, & routing
├── README.md                                    # Local installation & CLI tool documentation
├── assets/
│   └── templates/
│       ├── refactoring-plan.md                  # Working ledger for multi-step refactorings + Two-Hats parking lot
│       └── parallel-change-checklist.md         # Expand-DualWrite-Backfill-Migrate-Contract runbook
├── scripts/
│   ├── smell_scan.py                            # Zero-dep AST + heuristic code smell scanner (v1.1.0)
│   ├── step_guard.py                            # Baseline recorder, micro-step test runner, Two-Hats diff check
│   └── characterization_harness.py              # Golden-master snapshot harness for legacy untested seams
└── references/
    ├── catalog-index.md                         # Master 61-item alphabetical/chapter index, 1e aliases, & inverses
    ├── principles-and-testing.md                # Preface, Ch. 2, Ch. 4, Ch. 5: Principles, baby steps, CI, Testing
    ├── smells-to-refactorings.md                # Ch. 3: 24-row cheat sheet + deep smell diagnostics & exceptions
    ├── playbooks-and-compositions.md            # Ch. 1, 10, 12: 7 worked end-to-end architectural playbooks
    ├── ch06-first-set.md                        # Ch. 6: A First Set of Refactorings (11 items)
    ├── ch07-encapsulation.md                    # Ch. 7: Encapsulation (9 items)
    ├── ch08-moving-features.md                  # Ch. 8: Moving Features (9 items)
    ├── ch09-organizing-data.md                  # Ch. 9: Organizing Data (5 items)
    ├── ch10-simplifying-conditionals.md         # Ch. 10: Simplifying Conditional Logic (6 items)
    ├── ch11-refactoring-apis.md                 # Ch. 11: Refactoring APIs (10 items)
    └── ch12-dealing-with-inheritance.md         # Ch. 12: Dealing with Inheritance (11 items)
```

## Local Installation

Unzip `refactoring-skill.zip` and place the `refactoring/` folder into your agent's skill directory:

- **Claude Code**:
  - Global (all projects): `~/.claude/skills/refactoring/`
  - Project-scoped: `<repo>/.claude/skills/refactoring/`
- **OpenAI Codex CLI / Agent Skills**:
  - Global: `~/.codex/skills/refactoring/` or `~/.agents/skills/refactoring/`
- **Cursor**:
  - Copy into `.cursor/skills/refactoring/` (or reference `SKILL.md` from `.cursor/rules/`).
- **Gemini**:
  - Upload `refactoring-skill.zip` (or the `refactoring/` folder) via the **Skills Manager** UI.

## Quick CLI Usage (Python 3.9+ Standard Library Only)

```bash
# 1. Scan a file or directory for structural code smells (Markdown table or --json)
python3 scripts/smell_scan.py ./src --max-fn-lines 40 --max-params 4

# 2. Lock a green baseline before refactoring
python3 scripts/step_guard.py baseline --cmd "pytest -q"

# 3. Verify and record each atomic micro-step
python3 scripts/step_guard.py step --name "6.1 Extract Function: calculateBaseCharge" --cmd "pytest -q"

# 4. Audit git diff to ensure tests and production logic were not mixed under one hat
python3 scripts/step_guard.py check-hats

# 5. Record and verify characterization snapshots on legacy code before refactoring
python3 scripts/characterization_harness.py init-template --out cases.json
python3 scripts/characterization_harness.py record --manifest cases.json
python3 scripts/characterization_harness.py verify --manifest cases.json
```
