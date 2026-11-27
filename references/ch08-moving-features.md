# Chapter 8: Moving Features (9 Items)

Relocating functions, fields, statements, and loops so cohesive logic lives together, loops do one job each, and dead code disappears. Run static checks and tests at every `[Test]` checkpoint.

## 8.1 Move Function

- **1st Ed. Aliases**: Move Method
- **Motivation**: Good modularity means elements that change together live together. Move a function when it references data/functions in another module or class more often than its current home (*Feature Envy*), or un-nest an inner helper (`trackSummary` -> `top_calculateDistance`) so sibling functions can call it directly.

```javascript
// Before: overdraftCharge inside Account only reads this.type.* and this.daysOverdrawn
class Account { get bankCharge() { ... this.overdraftCharge ... } }

// After: moved onto AccountType where overdraft rules vary
class AccountType { overdraftCharge(daysOverdrawn) { ... } }
```

- **Worked Variants & Parameter Tradeoffs**:
  - *Un-nesting nested closures*: Before hoisting a nested function (`calculateDistance`) to top-level (`top_calculateDistance`), temporarily copy any inner helpers it uses (`distance`, `radians`) *inside* `calculateDistance` first so static analysis/linters prove zero remaining outer-closure variable captures before hoisting!
  - *Passing primitive vs. passing host reference*: Pass `daysOverdrawn` directly when the target needs only one value; pass `this` (`account`) when the target method needs multiple varying properties on the host object.
- **Mechanics**:
  1. Examine everything the function uses in its current context:
     - Nested helpers used *only* by it? Move them along with it (or inline first).
     - Reads fields on source object? Pass the source object (or specific primitives) as a parameter to the target.
     - Polymorphic method on a hierarchy? Check super/subclasses carefully before moving.
  2. Copy the function to the target context, adjust names and parameter references to fit the target domain, and verify static checks.
  3. Turn the source function into a thin delegating forwarder calling the target function. `[Test]`
  4. Apply `6.2 Inline Function` on the delegating forwarder so callers invoke the target directly (unless keeping a convenience delegate intentionally). `[Test]`

## 8.2 Move Field

- **Motivation**: Data structures are the backbone of a program; a poorly placed field forces callers everywhere to pass extra arguments and write awkward glue code. Move a field when it is always passed alongside another record or modified primarily by another class.

```javascript
// Before: discountRate sits on Customer while CustomerContract owns billing terms
class Customer { get discountRate() { return this._discountRate; } }

// After: discountRate lives on CustomerContract
class Customer { get discountRate() { return this._contract.discountRate; } }
```

- **Two Critical Traps (Ch. 8.2)**:
  1. **Constructor Initialization Order**: If `Customer` called `this._setDiscountRate(discountRate)` *before* `this._contract = new CustomerContract(...)`, delegating `_setDiscountRate` to `this._contract` throws `Cannot set property 'discountRate' of undefined`! Apply `8.6 Slide Statements` inside the constructor so target initialization precedes any setter call.
  2. **Moving a Field to a Shared Object (`Account._interestRate` -> shared `AccountType._interestRate`)**: If multiple `Account` instances share one `AccountType` and previously held *different* interest rates, moving the field silently changes observable behavior! **Mandatory Guard**: Keep `Account._interestRate` temporarily and insert `10.6 Introduce Assertion` (`assert(interestRate === this._type.interestRate)`) inside `Account`'s constructor (or log discrepancies in production for a grace period) to prove 100% of accounts match their type's rate before switching reads to `this._type.interestRate`!
- **Mechanics**:
  1. Ensure the source field is encapsulated (`6.6 Encapsulate Variable` / `7.1 Encapsulate Record`). `[Test]`
  2. Create the field and accessors on the target class/record (confirming target initialization precedes field writes, and asserting invariant equality if the target object is shared across multiple source instances). `[Test]`
  3. Compile/typecheck, then update the source class's accessors to delegate reads/writes to the target field. `[Test]`
  4. Migrate callers to access the target directly if desired, and delete the dead source field. `[Test]`

## 8.3 Move Statements into Function

- **Inverse**: `8.4 Move Statements to Callers`
- **Motivation**: Eliminate shotgun duplication when the exact same setup, formatting, or logging lines appear immediately before or after **every** call to a target function.

```javascript
// Before: every caller emits title right before emitPhotoData(p)
result.push(`<p>title: ${person.photo.title}</p>`);
result.push(emitPhotoData(person.photo));

// After: title emission folded inside emitPhotoData(aPhoto)
result.push(emitPhotoData(person.photo));
```

- **Mechanics**:
  1. If the repeated lines are separated from the call, use `8.6 Slide Statements` to move them adjacent to the call. `[Test]`
  2. Single caller: cut the statements from the caller, paste into the target function, and `[Test]`.
  3. Multiple callers: apply `6.1 Extract Function` on one call site (including both the repeated statements and the call) with a searchable temporary name (`zznew`). `[Test]`
  4. Replace every other call site's matching block with a call to `zznew` (`8.5 Replace Inline Code with Function Call`). `[Test]`
  5. Apply `6.2 Inline Function` of the original function into `zznew`, then rename `zznew` back to the original name (`6.5 Change Function Declaration`). `[Test]`

## 8.4 Move Statements to Callers

- **Inverse**: `8.3 Move Statements into Function`
- **Motivation**: Evolve function boundaries when a previously uniform action inside a shared function (`emitPhotoData`) now needs to behave differently for one caller while keeping the rest shared.

```javascript
// Before: location is printed inside emitPhotoData, blocking a new caller that formats location differently
function emitPhotoData(outStream, photo) {
  outStream.write(`<p>title: ${photo.title}</p>\n`);
  outStream.write(`<p>location: ${photo.location}</p>\n`);
}

// After: location statement peeled out to callers
```

- **Mechanics**:
  1. 1-2 simple callers (non-polymorphic): cut the varying statement from the callee and paste it into each caller. `[Test]`
  2. Many callers: apply `6.1 Extract Function` on all the *invariant* statements inside the callee under a temporary name (`zztmp`), leaving only the varying statement + call to `zztmp` in the original function. `[Test]`
  3. **Polymorphic Override Rule**: If the original method is overridden across subclasses (as in Ch. 10.4 `ExperiencedChinaRating`), extract the varying slice into its own hook method across *both* the superclass and every subclass so the outer method bodies become identical, delete the subclass duplicate overrides so subclasses inherit the superclass outer method `[Test]`, and only then peel the hook call up to the caller!
  4. Apply `6.2 Inline Function` on the original function across call sites one by one. `[Test after each]`
  5. Rename `zztmp` back to the original function name (`6.5 Change Function Declaration`). `[Test]`

## 8.5 Replace Inline Code with Function Call

- **Motivation**: Replace open-coded loops or expressions (`let appliesToMass = false; for(const s of states) if (s === "MA") appliesToMass = true;`) with an existing domain helper or standard library call (`states.includes("MA")`).
- **Accidental Duplication Litmus Test**: Before deduplicating inline code into an existing function, verify the match is **essential, not coincidental**! Ask: *"If this function's implementation evolves tomorrow, should this call site change with it?"* Your best clue is the function's **name** - if the existing function's name looks out of place in the caller's domain context, either rename the function or keep them separate.

```javascript
// Before
let appliesToMass = false;
for (const s of states) { if (s === "MA") appliesToMass = true; }

// After
appliesToMass = states.includes("MA");
```

- **Mechanics**:
  1. Confirm the existing function's domain intent, return value, edge-case handling, and side effects match the inline code identically.
  2. Replace the inline code with the function call. `[Test]`

## 8.6 Slide Statements

- **1st Ed. Aliases**: Consolidate Duplicate Conditional Fragments
- **Motivation**: Co-locate related statements (sliding variable declarations down to right above first use, grouping lines before `6.1 Extract Function`, or sliding identical head/tail lines *out of* or *into* `if/else` legs!) to improve clarity.

```javascript
// Before: declaration far from usage; duplicate chargeOrder(charge) tail in both branches
const pricingPlan = retrievePricingPlan();
const order = retreiveOrder();
let charge;
if (order.isRepeat) { discount = 20; chargeOrder(charge); }
else { discount = 0; chargeOrder(charge); }

// After: declarations slid adjacent to use; duplicate tail slid once after conditional
```

- **Safety Checklist (Must Hold Before Sliding)**:
  - Cannot slide a declaration above variables it references, nor slide a usage above its declaration.
  - Moving fragment must **not** modify any state read or modified by statements it crosses (unless commutative, like independent `total += 10; total += 5;`).
  - Moving fragment must **not** read any state modified by statements it crosses.
- **Mechanics**:
  1. Verify zero side-effect interference across every crossed statement (apply `11.1 Separate Query from Modifier` or `9.1 Split Variable` if blocked).
  2. Cut and paste statements to the target line (or out of / into every branch of an `if/else` block). `[Test]`
  3. **Fallback on Red (*Bill Wake's Swap Statement*)**: If sliding across 8 lines turns a test red, revert immediately and slide 1-2 lines at a time (`[Test]` after each hop) to pinpoint the interfering statement!

## 8.7 Split Loop

- **Motivation**: A loop doing two jobs (`youngest` AND `totalSalary`) forces future changes to modify both together and blocks extracting either calculation into its own function. Always split multi-purpose loops first, then optimize only if profiling ever demands it!

```javascript
// Before
let youngest = people[0] ? people[0].age : Infinity;
let totalSalary = 0;
for (const p of people) {
  if (p.age < youngest) youngest = p.age;
  totalSalary += p.salary;
}

// After (followed immediately by Slide Statements + Extract Function + Pipeline)
let totalSalary = 0;
for (const p of people) { totalSalary += p.salary; }

let youngest = people[0] ? people[0].age : Infinity;
for (const p of people) { if (p.age < youngest) youngest = p.age; }
```

- **Mechanics**:
  1. Copy the entire loop right below itself.
  2. Eliminate the duplicate calculations/side effects so each loop computes exactly one concern. `[Test]`
  3. Immediately follow up: apply `8.6 Slide Statements` to group each accumulator next to its loop, then `6.1 Extract Function` (and `8.8 Replace Loop with Pipeline`) on each loop! `[Test]`

## 8.8 Replace Loop with Pipeline

- **Motivation**: Express collection processing as a readable pipeline of declarative stages (`filter`, `map`, `flatMap`, `reduce`, `slice`) instead of tracking mutable loop state and `continue` branches.

```javascript
// Before
const names = [];
for (const i of input) {
  if (i.job === "programmer") names.push(i.name);
}

// After
const names = input
  .filter(i => i.job === "programmer")
  .map(i => i.name);
```

- **Mechanics**:
  1. Create a new variable assigned to the loop's source collection (`let loopItems = input;`), and iterate over `loopItems`. `[Test]`
  2. Take the outermost/topmost behavior inside the loop (e.g., header `slice(1)`, blank-line `.filter(line => line.trim() !== "")`, or `.map(...)` record split), append that pipeline operator onto `loopItems`, and delete that step from inside the loop body. `[Test after each stage]`
  3. Once all behavior lives in the pipeline, delete the loop and assign the final pipeline result directly to the target variable. `[Test]`

## 8.9 Remove Dead Code

- **Motivation**: Unused functions, unreachable conditional branches, and dead parameters add cognitive tax when reading or refactoring code; version control permanently remembers deleted code if ever needed again.

```javascript
// Before
if (false) { doSomethingThatUsedToMatter(); }
```

- **Mechanics**:
  1. Search across the codebase (including dynamic/string-based lookups, templates, and reflection configs) to confirm zero live references.
  2. Delete the dead code (and any obsolete comments or tests targeting solely the dead code). `[Test]`
