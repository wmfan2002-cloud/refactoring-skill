# Chapter 6: A First Set of Refactorings (11 Items)

Fowler's foundational toolkit: extracting and inlining functions/variables, evolving signatures and names, grouping functions around shared records, and splitting sequential processing phases. Run static checks and tests at every `[Test]` checkpoint.

## 6.1 Extract Function

- **1st Ed. Aliases**: Extract Method | **Inverse**: `6.2 Inline Function`
- **Motivation**: Separate *intent* (what the code accomplishes) from *implementation* (how it computes it). Extract whenever a reader must pause to deduce what a fragment does, or whenever a comment explains a block - even for 1-3 lines.

```javascript
// Before
function printOwing(invoice) {
  printBanner();
  let outstanding = calculateOutstanding();
  console.log(`name: ${invoice.customer}`);
  console.log(`amount: ${outstanding}`);
}

// After
function printOwing(invoice) {
  printBanner();
  let outstanding = calculateOutstanding();
  printDetails(invoice, outstanding);
}
function printDetails(invoice, outstanding) {
  console.log(`name: ${invoice.customer}`);
  console.log(`amount: ${outstanding}`);
}
```

- **Mechanics**:
  1. Create a new function named after **what** it does (if you cannot invent a meaningful name, do not extract). Use a nested function temporarily if helpful to test variable scope, or extract directly to sibling scope to expose variable dependencies early.
  2. Copy the extracted code into the target function.
  3. Inspect every local variable referenced inside the extracted code:
     - Read-only in extracted block: pass as a parameter.
     - Used *only* inside extracted block: `8.6 Slide Statements` its declaration into the block and move it inside.
     - Mutated inside extracted block and read afterward (single variable): initialize inside the extracted function and `return` the updated value (`const outstanding = calculateOutstanding(invoice)`).
     - **Two or more mutated locals needed afterward**: abort extraction for a moment! Apply `9.1 Split Variable`, `8.7 Split Loop`, or `7.4 Replace Temp with Query` first so each extracted function returns a single value.
  4. Compile/typecheck, then replace the original fragment with a call to the new function. `[Test]`
  5. Search for duplicate or similar inline code elsewhere and replace via `8.5 Replace Inline Code with Function Call`. `[Test]`

## 6.2 Inline Function

- **1st Ed. Aliases**: Inline Method | **Inverse**: `6.1 Extract Function`
- **Motivation**: Eliminate needless indirection when a function body is just as self-explanatory as its name, or consolidate a tangled cluster of poorly factored tiny helpers into one body before re-extracting along cleaner seams.
- **When NOT to Use**: Do not inline polymorphic methods overridden by subclasses, recursive functions, or complicated multi-exit functions.

```javascript
// Before
function rating(aDriver) { return moreThanFiveLateDeliveries(aDriver) ? 2 : 1; }
function moreThanFiveLateDeliveries(dvr) { return dvr.numberOfLateDeliveries > 5; }

// After
function rating(aDriver) { return aDriver.numberOfLateDeliveries > 5 ? 2 : 1; }
```

- **Mechanics**:
  1. Check that the function is **not polymorphic** (neither overridden in subclasses nor required by an interface).
  2. Find all callers.
  3. Replace each call with the function's body one call site at a time, adapting parameter names and mutating arguments carefully (if tricky, apply `8.4 Move Statements to Callers` one line at a time). `[Test after each call site]`
  4. Delete the function definition. `[Test]`

## 6.3 Extract Variable

- **1st Ed. Aliases**: Introduce Explaining Variable | **Inverse**: `6.4 Inline Variable`
- **Motivation**: Clarify dense arithmetic, boolean, or string expressions inside a single function by naming sub-expressions (also gives debuggers easy inspection hooks). *Note*: If the named concept makes sense across an entire class, prefer `6.1 Extract Function` (getter) instead so other methods can share it.

```javascript
// Before
return order.quantity * order.itemPrice -
  Math.max(0, order.quantity - 500) * order.itemPrice * 0.05 +
  Math.min(order.quantity * order.itemPrice * 0.1, 100);

// After
const basePrice = order.quantity * order.itemPrice;
const quantityDiscount = Math.max(0, order.quantity - 500) * order.itemPrice * 0.05;
const shipping = Math.min(basePrice * 0.1, 100);
return basePrice - quantityDiscount + shipping;
```

- **Mechanics**:
  1. Confirm the expression to extract has **no side effects**.
  2. Declare an immutable variable (`const` / `final`) set to a copy of the expression.
  3. Replace the original expression (and duplicate occurrences one by one) with the new variable. `[Test]`

## 6.4 Inline Variable

- **1st Ed. Aliases**: Inline Temp | **Inverse**: `6.3 Extract Variable`
- **Motivation**: Remove a temporary variable when its name says no more than the expression itself or when the temp obstructs extracting surrounding code.

```javascript
// Before
let basePrice = anOrder.basePrice;
return basePrice > 1000;

// After
return anOrder.basePrice > 1000;
```

- **Mechanics**:
  1. Check that the right-hand side of the assignment is free of side effects.
  2. Declare the variable immutable (`const` / `final`) if it isn't already and `[Test]` - proving it is assigned only once.
  3. Replace the first reference with the right-hand side expression. `[Test]`
  4. Repeat for remaining references, then delete the declaration and assignment. `[Test]`

## 6.5 Change Function Declaration

- **Aliases**: Rename Function, Rename Method, Add Parameter, Remove Parameter, Change Signature
- **Motivation**: Evolve the "joints" connecting software modules: give functions intention-revealing names (write a comment describing the purpose, then turn that comment into the name) and adjust parameters to decouple modules (e.g., passing `stateCode` instead of `aCustomer` so any state string works).

```javascript
// Simple rename / signature evolution
function inNewEngland(aCustomer) { return ["MA", "CT", "ME", "VT", "NH", "RI"].includes(aCustomer.address.state); }
// -> Migration ->
function inNewEngland(stateCode) { return ["MA", "CT", "ME", "VT", "NH", "RI"].includes(stateCode); }
```

- **Simple Mechanics** (narrow scope, static types, few callers):
  1. If removing a parameter, ensure it is unreferenced in the body.
  2. Update the declaration to the desired signature (if renaming AND changing parameters, do them in two separate steps).
  3. Update all references/callers. `[Test]` (If anything breaks or feels sprawling, revert immediately and switch to Migration Mechanics!)
- **Migration Mechanics** (wide caller fan-out, polymorphic hierarchies, or published APIs):
  1. Refactor the function body if needed (e.g., `6.3 Extract Variable` for the new parameter expression) so extraction is trivial.
  2. Apply `6.1 Extract Function` on the body to create the new signature (use a searchable temporary name like `xxNEWinNewEngland` if keeping the original name; optionally guard new parameters with `10.6 Introduce Assertion`). `[Test]`
  3. If the old function is a published external API, mark it `@deprecated` and pause until clients migrate.
  4. Apply `6.2 Inline Function` on the old forwarding function one caller (or small batch) at a time. `[Test after each]`
  5. Rename the temporary function back to the final name. `[Test]`

## 6.6 Encapsulate Variable

- **1st Ed. Aliases**: Self-Encapsulate Field, Encapsulate Field
- **Motivation**: Functions are easy to move or evolve because old functions can forward to new ones; raw data cannot forward! Wrapping any mutable variable whose scope exceeds a single function behind getter/setter functions creates an explicit choke point for access control, validation, refactoring, and immutability protection.

```javascript
// Before
let defaultOwner = { firstName: "Martin", lastName: "Fowler" };

// After (encapsulating both reference AND interior mutation via copy or record wrapper)
let defaultOwnerData = { firstName: "Martin", lastName: "Fowler" };
export function defaultOwner() { return { ...defaultOwnerData }; }
export function setDefaultOwner(arg) { defaultOwnerData = { ...arg }; }
```

- **Mechanics**:
  1. Create encapsulating getter and setter functions (avoid overloaded single-name getter/setters like `owner(val)`).
  2. Replace every read reference with a getter call and every assignment with a setter call. `[Test after each batch]`
  3. Restrict visibility of the raw variable (move to private module scope, mark `private`, or rename to `__privateOnly_x` to catch unmigrated references). `[Test]`
  4. **Value Encapsulation Check**: If the variable holds an object/array, prevent callers from mutating interior properties behind your back by returning a clone (`{ ...data }` / `slice()`) or wrapping with `7.1 Encapsulate Record`. `[Test]`

## 6.7 Rename Variable

- **Motivation**: Clear variable naming carries half the burden of readable code; invest maximum care in variables surviving beyond a single function call.

```javascript
// Constant / read-only export migration without breaking callers
const companyName = "Acme Gooseberries";
const cpyNm = companyName; // migrate readers from cpyNm -> companyName, then delete cpyNm
```

- **Mechanics**:
  1. **Function-local variable/parameter**: update declaration and all local references, then `[Test]`.
  2. **Widely shared mutable variable**: apply `6.6 Encapsulate Variable` first! Rename the private backing variable and accessors safely (and usually keep it encapsulated afterward). `[Test]`
  3. **Constant or read-only module export**: declare the new constant first, set `const oldName = newName;`, update readers incrementally `[Test]`, and remove `oldName`.

## 6.8 Introduce Parameter Object

- **Motivation**: Replace a data clump of 2+ parameters (`startDate, endDate` or `min, max`) traveling together across functions with a single Value Object (`DateRange`, `NumberRange`), shrinking parameter lists, unifying field naming, and unlocking behavior migration (`range.contains(temp)`).

```javascript
// Before
function readingsOutsideRange(station, min, max) {
  return station.readings.filter(r => r.temp < min || r.temp > max);
}

// After
function readingsOutsideRange(station, range) {
  return station.readings.filter(r => !range.contains(r.temp));
}
```

- **Mechanics**:
  1. Create an immutable class/value structure for the grouped parameters if none exists yet. `[Test]`
  2. Use `6.5 Change Function Declaration` to append the new parameter (`range = null`) alongside the old parameters. `[Test]`
  3. Adjust each caller to pass an instance of the new parameter object. `[Test]`
  4. Replace references to the old parameters inside the function body one field at a time (`range.max`, then `range.min`), deleting each superseded parameter. `[Test]`
  5. Look for range/clump operations in callers/callees and move them into the new class (`8.1 Move Function`). `[Test]`

## 6.9 Combine Functions into Class

- **Motivation**: Group functions that repeatedly pass around and manipulate the same shared data structure into a single class, making shared state explicit, trimming parameter lists, and keeping derived getters consistent even when underlying fields mutate.

```javascript
// Before
function base(aReading) { ... }
function taxableCharge(aReading) { ... }

// After
class Reading {
  constructor(data) { this._customer = data.customer; this._quantity = data.quantity; ... }
  get baseCharge() { return baseRate(this.month, this.year) * this.quantity; }
  get taxableCharge() { return Math.max(0, this.baseCharge - taxThreshold(this.year)); }
}
```

- **Mechanics**:
  1. Apply `7.1 Encapsulate Record` to the shared data structure (or `6.8 Introduce Parameter Object` first if loose fields). `[Test]`
  2. Take each function using that record and move it into the new class via `8.1 Move Function`, removing parameters now accessible on `this`. `[Test]`
  3. Extract any duplicated inline client calculations with `6.1 Extract Function` and move them into the class too. `[Test]`

## 6.10 Combine Functions into Transform

- **Motivation**: Gather scattered derived-data calculations over **immutable / read-only** records into a single `enrichX` (same logical type + derived fields) or `transformX` (new shape) pipeline function so derived logic lives in one discoverable place.
- **When NOT to Use**: Avoid if client code mutates source fields after enrichment - derived fields on the enriched object would silently go stale! Use `6.9 Combine Functions into Class` when source data is mutable.

```javascript
// Before: scattered baseCharge and taxableCharge formulas across clients
// After:
function enrichReading(original) {
  const result = structuredClone(original);
  result.baseCharge = calculateBaseCharge(result);
  result.taxableCharge = Math.max(0, result.baseCharge - taxThreshold(result.year));
  return result;
}
```

- **Mechanics**:
  1. Create `enrichX(original)` that deep-clones the input record and returns the clone. **Write a dedicated unit test asserting `original` remains completely unchanged after calling `enrichX(original)`.** `[Test]`
  2. Pick one calculation, move it into `enrichX` to attach `result.field = ...`, and update client sites to read `aReading.field`. `[Test]`
  3. Repeat for all remaining derived calculations, cleaning up dead local temps via `6.4 Inline Variable`. `[Test]`

## 6.11 Split Phase

- **Motivation**: Separate a module or function doing two sequential jobs over different data/concepts (e.g., parsing raw text vs. pricing, or domain calculation vs. HTML formatting) so you can modify or test one phase without loading the other into working memory.

```javascript
// Before: product pricing and shipping math tangled together
function priceOrder(product, quantity, shippingMethod) { ... }

// After: Phase 1 produces immutable intermediate priceData; Phase 2 applies shipping
function priceOrder(product, quantity, shippingMethod) {
  const priceData = calculatePricingData(product, quantity);
  return applyShipping(priceData, shippingMethod);
}
```

- **Mechanics**:
  1. Apply `6.1 Extract Function` to isolate the second phase into its own function. `[Test]`
  2. Introduce an empty intermediate data structure (`const priceData = {};`) passed as an additional parameter to the second-phase function. `[Test]`
  3. Inspect each parameter of the second-phase function one by one:
     - Created or used by Phase 1 (`basePrice`, `quantity`, `discount`): populate it as a property on the intermediate structure and remove it from the parameter list. `[Test after each parameter]`
     - Used *only* by Phase 2 (`shippingMethod`): leave as a direct parameter to Phase 2.
     - Should not enter Phase 2 at all: extract its result into an intermediate field in Phase 1 (`8.4 Move Statements to Callers`).
  4. Apply `6.1 Extract Function` on the Phase 1 setup code, returning the completed intermediate data structure. `[Test]`
