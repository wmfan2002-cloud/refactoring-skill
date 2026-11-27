---
name: refactoring
description: Behavior-preserving code refactoring workflow, code smell diagnosis, and step-by-step mechanics based on Martin Fowler's Refactoring (2nd Edition). Use whenever the user asks to refactor code, clean up legacy modules, eliminate code smells or technical debt, split large functions or classes, simplify complex conditionals, encapsulate mutable state, redesign APIs or inheritance hierarchies, or prepare existing code before adding a feature or fixing a bug.
metadata:
  version: 1.1.0
compatibility: Agent-agnostic (Claude Code, Codex, Cursor, Gemini). Bundled CLI scripts in scripts/ use Python 3.9+ standard library only (zero external dependencies).
---
# Refactoring

Transform internal software structure through small, verifiable, behavior-preserving micro-steps based on Martin Fowler's *Refactoring: Improving the Design of Existing Code (2nd Edition)*. Keep the system compiling and passing tests at every intermediate checkpoint so design quality improves continuously without debugging marathons.

## When to Use

- Restructuring existing functions, classes, modules, or data types to improve clarity and modifiability while keeping observable behavior unchanged.
- Diagnosing and curing concrete code smells (long functions, duplicated logic, mutable/global data, divergent change, shotgun surgery, feature envy, data clumps, primitive obsession, repeated switches, temporary fields, or misused inheritance).
- Executing **preparatory refactoring** right before adding a feature or fixing a bug ("make the change easy, then make the easy change").
- Executing **comprehension** or **litter-pickup refactoring** when untangling unfamiliar or legacy codebases.
- Performing structural code reviews that map defects to named Fowler refactorings and safe migration steps.

### When Not to Refactor

- **Untouched code hidden behind a clean API**: If you do not need to read, understand, or modify the internals of an ugly module, leave it alone.
- **Rewrite is genuinely cheaper**: Choose a clean rewrite only when behavior is small or fully specified by black-box tests and incremental transformation clearly costs more than replacement.
- **Zero verification signal on fragile code**: Never run multi-file manual restructuring blind. Establish characterization tests at seams first (see `references/principles-and-testing.md`) or restrict edits strictly to compiler/LSP-verified AST moves.

## Core Discipline (Six Invariants)

1. **Never wear both hats at once**: Keep the *Refactoring Hat* (restructuring only, zero observable behavior changes, no new feature tests) strictly separate from the *Feature/Bugfix Hat*. Park newly discovered bugs or feature ideas in a checklist until tests are green.
2. **Compile-Test-Commit rhythm**: Run static checks and relevant tests before starting and after *every* atomic refactoring move. Commit locally after each green move, then squash micro-commits into cohesive logical commits before pushing.
3. **Revert on red & fall back to baby steps (Ch. 5.1)**: Take slightly larger steps when confident, but if any step breaks a test and the slip is not obvious within 30 seconds, **revert immediately to the last green state** and re-execute using the catalog's finest-grained baby steps.
4. **Separate intent from implementation**: Extract and name code after *what* it accomplishes in domain terms, never *how* its mechanics work internally. Use consistent return-accumulator naming (`result`) and, in dynamically typed languages, type-revealing parameter names (`aPerformance`, `aCustomer`).
5. **Migrate wide-scope changes incrementally**: Never break callers across a codebase in one giant edit when fan-out is wide; introduce forwarding wrappers (`Migration Mechanics`) or `Expand-Contract` phases so every step stays green.
6. **Honor YAGNI over speculative generality**: Introduce abstractions, parameters, or polymorphism only for variations required today, never for hypothetical future needs.

## Steps

### 1. Establish the Baseline & Testing Gate

1. Run the target test suite, typechecker, and linter to confirm a clean starting baseline (`python3 scripts/step_guard.py baseline --cmd "<test_cmd>"` when shell execution is available).
2. Audit test coverage around the target code:
   - Probe boundary conditions (empty collections `[]`, `0`, negative numbers, `null`/undefined, `threshold - 1` / `threshold` / `threshold + 1`) using **fresh `beforeEach` fixtures** rather than shared mutable instances.
   - **Prune undefined-contract crash tests (Ch. 4.6)**: Delete or isolate tests that probe accidental runtime crashes (`TypeError`) on malformed internal inputs outside observable contracts so refactoring is not handcuffed to preserving undefined crash details.
3. If legacy code lacks tests, load `references/principles-and-testing.md`, capture golden-master behavior at an existing seam (`python3 scripts/characterization_harness.py`), and run a **fault-injection check** (temporarily mutate one production operator to prove a test turns red, then revert).

### 2. Diagnose Smells & Select Architectural Tradeoffs

Scan the target files (`python3 scripts/smell_scan.py <path>` for structural hotspots, plus human semantic reading) and apply the **Rule of Three**. Consult `references/smells-to-refactorings.md` for all 24 smells and `references/catalog-index.md` for fast lookup across all 61 refactorings and 1st-edition aliases.

Use these four Fowler decision rules when choosing target structures:

| Architectural Choice | Prefer Option A When | Prefer Option B When |
| --- | --- | --- |
| `Combine Functions into Class` vs. `Combine Functions into Transform` | Source data can be mutated after creation (getters keep derived values live and consistent) | Input record is strictly read-only / immutable pipeline data (`enrichX` / `transformX`) |
| `Change Reference to Value` vs. `Change Value to Reference` | Representing immutable domain quantities/ranges (`Money`, `DateRange`) safe to copy freely | Representing a shared mutable real-world entity (`Customer`, `Account`, `CatalogItem`) needing one canonical instance |
| `Replace Type Code with Subclasses` vs. `Replace Subclass with Delegate` | Type is fixed for object lifetime and class has no competing inheritance axis | Category changes dynamically at runtime OR class already subclasses along another axis |
| `Replace Parameter with Query` vs. `Replace Query with Parameter` | Callee already holds the source object and computing internally simplifies callers | Pulling data inside callee creates unwanted global/singleton/layer coupling (keep callee pure) |

### 3. Choose Execution Strategy by Blast Radius

- **Direct (Simple) Mechanics**: Local variables, private helpers, or narrow-scope functions/fields with a handful of callers updatable in one pass (lean on compiler errors in statically typed languages).
- **Migration Mechanics** (wide fan-out, polymorphic methods, or published APIs):
  1. Refactor internals if needed, then extract the desired target function/class under a temporary searchable name (`zz_newName` or `appleSauce` when colliding with an existing local temp).
  2. Turn the original symbol into a thin delegating wrapper (add `@deprecated` if externally published). Run tests.
  3. Migrate callers one by one (`Inline Function` on the wrapper), testing after each batch.
  4. Delete the wrapper and rename `zz_newName` into its final name.
- **Parallel Change / Expand-Contract** (databases, JSON wire schemas, cross-repo contracts; template in `assets/templates/parallel-change-checklist.md`):
  1. *Expand* schema -> 2. *Dual-write* & backfill -> 3. *Migrate readers* -> 4. *Contract* dead fields.

### 4. Execute Micro-Steps & Composite Playbooks

For multi-step restructurings, copy `assets/templates/refactoring-plan.md` as your working checklist and consult `references/playbooks-and-compositions.md` plus the matching chapter reference (`references/ch06-*.md` through `references/ch12-*.md`).

#### Canonical Ch. 1 Three-Stage Pipeline (Tangled Monolith -> Clean Architecture)

1. **Stage A - Decompose & Untangle Temps**:
   - `Split Variable` for reassigned temps -> `Slide Statements` to group declarations with uses -> `Split Loop` to separate mixed accumulations -> `Extract Function` + `Replace Temp with Query` so helpers stop threading local temps (keep internal money/unit math in integer base units and push `/ 100` formatting inside explicit functions like `usd()`).
2. **Stage B - Split Phase**:
   - Apply `Split Phase` to separate calculation/parsing (Phase 1) from formatting/rendering/I/O (Phase 2) via an immutable intermediate data structure (`statementData`).
3. **Stage C - Polymorphism or Delegation**:
   - Replace repeated type-code switches or base-and-variant overrides inside Phase 1 using `Replace Constructor with Factory Function` + `Replace Type Code with Subclasses` (or `Replace Subclass with Delegate`) + `Replace Conditional with Polymorphism`.

After each micro-step, verify tests stay green (`python3 scripts/step_guard.py step --name "<Catalog Name>" --cmd "<test_cmd>"`) and audit `check-hats` so test assertions and production logic are not silently altered in the same step.

### 5. Final Verification & Audit Handoff

1. Run the full test suite, typechecker, and linter; sweep any orphaned helpers/fields with `Remove Dead Code`.
2. Confirm public signatures, return shapes, error contracts, and side-effect ordering remain preserved.
3. Summarize the completed sequence using exact Fowler catalog names so reviewers can trace every structural step.

## Bundled CLI Scripts

All scripts in `scripts/` use Python 3.9+ standard library only and support `--help` and `--version`:

- `python3 scripts/smell_scan.py <path> [--json] [--max-fn-lines 40] [--max-params 4]`: Scans Python (AST) and JS/TS/Go/Java/Rust/C# files for Long Functions, Long Parameter Lists, Flag Arguments, Deep Nesting, Repeated Switches, deduplicated Data Clumps, Temporary Fields, Message Chains, Deodorant Comment Density, Global Mutable State, and Large Classes.
- `python3 scripts/step_guard.py <baseline|step|check-hats|status> ...`: Records baseline test state, verifies and logs each named refactoring micro-step, audits git diffs for Two-Hats violations, and guides fast rollback on red steps.
- `python3 scripts/characterization_harness.py <init-template|record|verify> --manifest <cases.json>`: Captures golden-master outputs across boundary test matrices before touching legacy code and verifies zero behavioral drift after each refactoring step.

## Reference Files & Templates

Load only the specific reference(s) needed for your current refactoring target:

- `references/catalog-index.md`: **Master 61-Refactoring Index** - Alphabetical & chapter lookup, inverse moves, 1st-edition (1999) alias mapping, and `refactoring.com` slugs.
- `references/principles-and-testing.md`: **Preface, Ch. 2, Ch. 4 & Ch. 5** - Consultant parable, Two Hats, Design Stamina Hypothesis, baby-steps fallback law, static vs. dynamic language rules, characterization value-fill & fault-injection loop, 4-phase test lifecycle, pruning crash tests, and over-testing smell.
- `references/smells-to-refactorings.md`: **Ch. 3** - Master 24-smell cheat sheet table, structural symptoms, legitimate exceptions, intra-class deduplication, and ordered catalog remedies.
- `references/playbooks-and-compositions.md`: **Ch. 1 & Multi-Move Pipelines** - 7 worked end-to-end architectural playbooks (including Ch. 1 micro-moves, `Rating` base-and-variant polymorphism, `SpeciesDelegate` full hierarchy delegation, and `Scroll` ID-splitting).
- `references/ch06-first-set.md`: **Ch. 6 (11 items)** - `Extract/Inline Function`, `Extract/Inline Variable`, `Change Function Declaration`, `Encapsulate/Rename Variable`, `Introduce Parameter Object`, `Combine Functions into Class/Transform`, `Split Phase`.
- `references/ch07-encapsulation.md`: **Ch. 7 (9 items)** - `Encapsulate Record/Collection`, `Replace Primitive with Object`, `Replace Temp with Query`, `Extract/Inline Class`, `Hide Delegate`, `Remove Middle Man`, `Substitute Algorithm`.
- `references/ch08-moving-features.md`: **Ch. 8 (9 items)** - `Move Function/Field`, `Move Statements into Function / to Callers`, `Replace Inline Code with Function Call`, `Slide Statements`, `Split Loop`, `Replace Loop with Pipeline`, `Remove Dead Code`.
- `references/ch09-organizing-data.md`: **Ch. 9 (5 items)** - `Split Variable`, `Rename Field`, `Replace Derived Variable with Query`, `Change Reference to Value`, `Change Value to Reference`.
- `references/ch10-simplifying-conditionals.md`: **Ch. 10 (6 items)** - `Decompose/Consolidate Conditional`, `Replace Nested Conditional with Guard Clauses`, `Replace Conditional with Polymorphism`, `Introduce Special Case`, `Introduce Assertion`.
- `references/ch11-refactoring-apis.md`: **Ch. 11 (10 items)** - `Separate Query from Modifier`, `Parameterize Function`, `Remove Flag Argument`, `Preserve Whole Object`, `Replace Parameter <-> Query`, `Remove Setting Method`, `Replace Constructor with Factory Function`, `Replace Function <-> Command`.
- `references/ch12-dealing-with-inheritance.md`: **Ch. 12 (11 items)** - `Pull Up / Push Down Method/Field/Constructor Body`, `Replace Type Code with Subclasses`, `Remove Subclass`, `Extract Superclass`, `Collapse Hierarchy`, `Replace Subclass/Superclass with Delegate`.
- `assets/templates/refactoring-plan.md` & `assets/templates/parallel-change-checklist.md`: Copyable runbooks for complex multi-step or schema-migrating refactorings.

## Gotchas

- **Mutating arrays/records through getters**: Encapsulating a field (`get courses() { return this._courses; }`) fails if callers invoke `.push()` or in-place `.sort()`. Always return a defensive copy or read-only view (`Encapsulate Collection` / `Encapsulate Record`).
- **Replacing snapshot temps with queries**: Never apply `Replace Temp with Query` to a variable capturing pre-mutation state (`const oldBalance = account.balance; account.withdraw(x);`). Queries re-evaluate live state and change behavior.
- **Moving a field onto a shared object (`8.2 Move Field`)**: Before moving `Account._interestRate` onto a shared `AccountType`, add `Introduce Assertion` (`assert(rate === this._type.interestRate)`) to verify all accounts of the same type actually hold identical rates; otherwise moving the field silently alters behavior.
- **Sliding statements across hidden side effects**: Before `Slide Statements` or `Split Loop`, verify neither skipped functions nor property getters mutate or read shared state; if a multi-line slide turns red, fall back to single-line swaps.
- **Infinite recursion when delegating `super` overrides (`12.10`)**: When moving a subclass method that called `super.basePrice` onto a delegate, calling `this._host.basePrice` recurses infinitely. Either extract `_privateBasePrice` on the host or pass the host result into `delegate.extendBasePrice(base)`.
- **Putting side effects inside assertions**: `Introduce Assertion` documents internal programmer invariants only (prefer placing them in setters at point of entry); never validate untrusted external input or mutate state inside `assert(...)`.
