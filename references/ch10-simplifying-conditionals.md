# Chapter 10: Simplifying Conditional Logic (6 Items)

Conditional logic accounts for most accidental complexity in codebases. Use these six refactorings to surface *why* code branches, flatten nested edge checks, replace repeated switches and variant tangles with polymorphism, banish repeated null/sentinel checks, and turn hidden assumptions into assertions. Run static checks and tests at every `[Test]` checkpoint.

## 10.1 Decompose Conditional

- **Motivation**: Long conditional expressions and bulky `then`/`else` legs tell you *how* conditions evaluate without telling you *why*. Extracting condition and branch legs turns opaque math/boolean logic into a readable domain sentence.

```javascript
// Before
if (!aDate.isBefore(plan.summerStart) && !aDate.isAfter(plan.summerEnd))
  charge = quantity * plan.summerRate;
else
  charge = quantity * plan.regularRate + plan.regularServiceCharge;

// After
charge = summer() ? summerCharge() : regularCharge();
```

- **Mechanics**:
  1. Apply `6.1 Extract Function` on the condition expression (`summer()`). `[Test]`
  2. Apply `6.1 Extract Function` on the `then` branch (`summerCharge()`) and the `else` branch (`regularCharge()`). `[Test]`

## 10.2 Consolidate Conditional Expression

- **Motivation**: Merge sequential or nested `if` checks that all lead to the **exact same** result into a single compound expression (`||` / `&&`), setting up `6.1 Extract Function` to name the unified domain rule (`isNotEligibleForDisability(anEmployee)`).
- **When NOT to Use**: Leave checks separate if they represent genuinely independent business rules that merely *happen* to return `0` today and should not evolve together, or if condition checks have side effects.

```javascript
// Before
if (anEmployee.seniority < 2) return 0;
if (anEmployee.monthsDisabled > 12) return 0;
if (anEmployee.isPartTime) return 0;

// After
if (isNotEligibleForDisability(anEmployee)) return 0;
function isNotEligibleForDisability(emp) {
  return emp.seniority < 2 || emp.monthsDisabled > 12 || emp.isPartTime;
}
```

- **Mechanics**:
  1. Ensure none of the condition checks have side effects.
  2. Combine two checks at a time using `||` (sequential `if`s returning same value) or `&&` (nested `if`s with no `else`). `[Test after each]`
  3. Apply `6.1 Extract Function` on the combined boolean condition. `[Test]`

## 10.3 Replace Nested Conditional with Guard Clauses

- **Motivation**: Conditional expressions come in two flavors:
  - *Symmetric alternatives* where both `then` and `else` are part of normal behavior -> keep `if ... else ...`.
  - *Unusual / edge conditions* that must be checked and exited early before normal processing -> use **Guard Clauses** (`if (isDead) return ...;`)! Single-exit-point dogma forces contrived mutable `result` temps and deep indentation that hides the main path.

```javascript
// Before
function payAmount(employee) {
  let result;
  if (employee.isSeparated) { result = { amount: 0, reasonCode: "SEP" }; }
  else {
    if (employee.isRetired) { result = { amount: 0, reasonCode: "RET" }; }
    else { result = someFinalComputation(employee); }
  }
  return result;
}

// After
function payAmount(employee) {
  if (employee.isSeparated) return { amount: 0, reasonCode: "SEP" };
  if (employee.isRetired) return { amount: 0, reasonCode: "RET" };
  return someFinalComputation(employee);
}
```

- **Inverting Conditions Safely (De Morgan Two-Step)**:
  When a function wraps its entire normal body inside `if (capital > 0) { if (interestRate > 0 && duration > 0) { ... } }`:
  1. Invert one condition first by wrapping literally in `!(...)` (`if (!(interestRate > 0 && duration > 0)) return result;`) and `[Test]`!
  2. Simplify the negated boolean via De Morgan's laws (`if (interestRate <= 0 || duration <= 0) return result;`) and `[Test]`!
  3. Merge adjacent `return 0` guards via `10.2 Consolidate Conditional Expression` and delete any dual-purpose `let result = 0` variable!
- **Mechanics**:
  1. Select the outermost check representing an early-exit condition and replace it with a flat guard clause returning immediately. `[Test]`
  2. Repeat for each nested guard condition, deleting artificial mutable `result` variables once branches return directly. `[Test]`
  3. Consolidate adjacent guards returning identical results via `10.2 Consolidate Conditional Expression`. `[Test]`

## 10.4 Replace Conditional with Polymorphism

- **Motivation**: Eliminate duplicated type switches AND untangle "standard behavior + special variant" conditionals so readers can understand the base logic without wading through variant exceptions.
- **Two Distinct Polymorphism Modes (Ch. 10.4)**:
  1. **Type-Code Dispatch (`Bird` -> `EuropeanSwallow`, `AfricanSwallow`, `NorwegianBlueParrot`)**: Every caller dispatches across mutually exclusive variants; the base `Bird` class holds fallback `"unknown"` / `null` or throws an abstract trap. During migration, replace each migrated `case` in the superclass `switch` with `throw "oops"` temporarily before deleting the `switch` to prove subclass routing works!
  2. **Base-and-Variant / "Programming by Difference" (`Rating` -> `ExperiencedChinaRating`)**: Base `Rating` implements the complete normal voyage algorithm while `ExperiencedChinaRating extends Rating` overrides only the specific sub-factors that differ (`super.captainHistoryRisk - 2`). When one conditional mixes two concerns (`voyageAndHistoryLengthFactor`), extract the mixed method with `"And"` in its name first, override in the subclass, then extract `historyLengthFactor` in both classes and apply `8.4 Move Statements to Callers` to separate them cleanly! *(See `references/playbooks-and-compositions.md` Playbook 7.)*

```javascript
// Mode 1: Type-code dispatch
class Bird { get plumage() { return "unknown"; } get airSpeedVelocity() { return null; } }
class EuropeanSwallow extends Bird { get plumage() { return "average"; } get airSpeedVelocity() { return 35; } }

// Mode 2: Base-and-Variant ("Programming by Difference")
class Rating { get captainHistoryRisk() { ... } }
class ExperiencedChinaRating extends Rating {
  get captainHistoryRisk() { return Math.max(super.captainHistoryRisk - 2, 0); }
}
```

- **Mechanics**:
  1. If polymorphic classes do not exist yet, create them alongside a factory function (`11.8 Replace Constructor with Factory Function` + `12.6 Replace Type Code with Subclasses` or `12.10 Replace Subclass with Delegate`). `[Test]`
  2. Move the conditional function into the superclass via `8.1 Move Function` if it isn't already there. `[Test]`
  3. Pick one subclass, create a method overriding the conditional method, copy that subclass's leg into it, and delete (or trap with `throw "oops"`) that leg in the superclass. `[Test]`
  4. Repeat for each subclass until only the default/base case remains in the superclass. `[Test]`

## 10.5 Introduce Special Case

- **1st Ed. Aliases**: Introduce Null Object
- **Motivation**: Eliminate duplicated `if (aCustomer === "unknown")` or `if (user == null)` checks scattered across dozens of files by returning a **Special Case** object, frozen literal, or enriched transform record carrying all default behaviors (`name: "occupant"`, `billingPlan: basic`, `isUnknown: true`).

```javascript
// Before: scattered across many clients
const customerName = aCustomer === "unknown" ? "occupant" : aCustomer.name;

// After: site.customer returns new UnknownCustomer() (or frozen literal) when unknown
const customerName = aSite.customer.name;
```

- **Three Implementation Variants & Subtle Edge Cases**:
  - *Class (`class UnknownCustomer`)*: Best when callers also invoke setters (`aCustomer.billingPlan = newPlan` -> implement a **no-op setter** `set billingPlan(arg) { /* ignore */ }` so Special Case stays immutable!) or nested Special Cases (`get paymentHistory() { return new NullPaymentHistory(); }`).
  - *Object Literal (`createUnknownCustomer()`)*: Lightweight and clean when clients only read properties - wrap with `Object.freeze(...)` so shared/literal defaults cannot be mutated!
  - *Transform (`enrichSite`)*: In read-only JSON pipelines (`6.10 Combine Functions into Transform`), replace `"unknown"` with `{ name: "occupant", billingPlan: registry.billingPlans.basic, paymentHistory: { weeksDelinquentInLastYear: 0 }, isUnknown: true }`.
  - **Custom-Caller Retention Rule**: If 23 callers want `"occupant"` while 1 caller wants `"unknown occupant"`, do **not** bloat `UnknownCustomer` for a one-off UI string - keep `const name = aCustomer.isUnknown ? "unknown occupant" : aCustomer.name;` at that single oddball call site!
- **Mechanics**:
  1. Add `get isUnknown() { return false; }` to the normal subject class/structure.
  2. Create the Special Case class/literal with `get isUnknown() { return true; }` initially.
  3. Extract the repeated comparison into `function isUnknown(arg)` (adding a temporary runtime trap `if (!(arg instanceof Customer || arg === "unknown")) throw new Error(...)` in dynamic languages!) and update all check sites to call `isUnknown(arg)`. `[Test]`
  4. Change the data source (`Site.customer`) to return the Special Case instance instead of `"unknown"`, and update `isUnknown(arg)` to return `arg.isUnknown`. `[Test]`
  5. Inspect every `isUnknown(...)` client call site: move its standard default behavior onto `UnknownCustomer` one property at a time, replacing the client conditional with a direct property/method call! `[Test after each]`
  6. Apply `6.2 Inline Function` on `isUnknown` once all check sites are migrated (retaining `aCustomer.isUnknown` for any genuine oddball caller). `[Test]`

## 10.6 Introduce Assertion

- **Motivation**: Communicate and enforce **internal program invariants** (`assert(this.discountRate >= 0)`). Assertions tell human readers what state is guaranteed at a given line and fail fast close to the root bug.
- **Golden Rules & Placement Strategy**:
  - **Fail at Point of Entry**: If `applyDiscount` assumes `this.discountRate >= 0`, ask *where* that negative value could originate - placing `assert(null === aNumber || aNumber >= 0)` inside `set discountRate(aNumber)` catches the bug the instant bad state enters rather than 20 calls later! (If attaching an assertion inside a ternary `a ? b : c`, rewrite to `if/else` first.)
  - Never use assertions to validate untrusted **external** inputs (API payloads, user forms, files) - write proper error-handling logic at system boundaries instead!
  - Never put side effects inside `assert(...)`, and assert only invariants *essential* for correct execution.

```javascript
// Placed at point of entry (setter) rather than only at downstream calculation:
set discountRate(aNumber) {
  assert(null === aNumber || aNumber >= 0);
  this._discountRate = aNumber;
}
```

- **Mechanics**:
  1. Spot an implicit invariant assumed to hold true, trace where that state enters, and add a side-effect-free `assert(...)` at the setter/assumption point. `[Test]`
