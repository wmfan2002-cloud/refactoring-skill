# Refactoring Execution Plan: <Target Module / Feature>

## 1. Scope & Motivation

- **Trigger**: [ ] Preparatory (before feature/fix) | [ ] Comprehension | [ ] Litter-Pickup | [ ] Planned Debt Paydown
- **Target Files**:
  - `<path/to/file>`
- **Out-of-Scope / Untouched Interfaces**:
  - `<public APIs or modules intentionally left untouched>`

## 2. Baseline Verification Gate

- **Test Command**: `<e.g., npm test / pytest -q / go test ./...>`
- **Static Check Command**: `<e.g., tsc --noEmit / ruff check / cargo check>`
- **Baseline Status**: [ ] Green (`<N>` tests passing in `<T>`s)
- **Characterization / Boundary Coverage Added Before Refactoring**:
  - [ ] Empty / zero / null inputs covered
  - [ ] Boundary edges covered
  - [ ] Fault-injection check verified (mutating target line turns test red)

## 3. Diagnosed Code Smells & Strategy

| Location (`file:line`) | Code Smell (Ch. 3) | Target Refactoring Chain | Mechanics Mode (`Direct` / `Migration` / `Expand-Contract`) |
| --- | --- | --- | --- |
| `<file:line>` | `<e.g., Long Function +Mutable Data>` | `<e.g., Split Variable -> Split Loop -> Extract Function -> Split Phase>` | `<Direct / Migration>` |

## 4. Atomic Micro-Step Ledger (Refactoring Hat Only)

Execute one row at a time. Run the verification gate after every row; revert immediately if red.

- [ ] **Step 1**: `<Catalog Number & Name>` - `<concrete symbol/target>` -> `[Test Green]`
- [ ] **Step 2**: `<Catalog Number & Name>` - `<concrete symbol/target>` -> `[Test Green]`
- [ ] **Step 3**: `<Catalog Number & Name>` - `<concrete symbol/target>` -> `[Test Green]`
- [ ] **Step 4**: `8.9 Remove Dead Code` - `<sweep temporary zz_ wrappers or unused locals>` -> `[Test Green]`

## 5. Two-Hats Parking Lot (Do NOT Fix During Refactoring Steps)

Record latent bugs, edge-case behavior questions, or follow-up feature tasks discovered while reading code. Address these **only** after all refactoring steps above finish on a green suite.

- **Latent Bugs Found** (write failing regression test first under Bugfix Hat):
  - `<none>`
- **Deferred Feature / Optimization Ideas**:
  - `<none>`
