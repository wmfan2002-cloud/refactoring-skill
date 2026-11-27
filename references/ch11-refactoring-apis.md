# Chapter 11: Refactoring APIs (10 Items)

Modules and functions meet at APIs. Use these 10 refactorings to separate queries from state mutations, right-size parameter lists, eliminate boolean mode flags, lock down immutability, wrap constructors behind factories, and promote/demote Command Objects. Run static checks and tests at every `[Test]` checkpoint.

## 11.1 Separate Query from Modifier

- **Motivation**: **Command-Query Separation**: functions that return a value without observable side effects can be called anywhere, reordered safely, and tested effortlessly. Split any function that both answers a question and mutates state/triggers alarms! *(Note: transparent caching does not count as an observable side effect; concurrent atomic `pop` is a deliberate concurrency exception.)*

```javascript
// Before
function alertForMiscreant(people) {
  for (const p of people) {
    if (p === "Don") { setOffAlarms(); return "Don"; }
  }
  return "";
}

// After
function findMiscreant(people) {
  for (const p of people) { if (p === "Don") return "Don"; }
  return "";
}
function alertForMiscreant(people) {
  if (findMiscreant(people) !== "") setOffAlarms();
}
```

- **Mechanics**:
  1. Copy the function and name it after the value it returns (`findMiscreant`), removing all side effects from the new query. `[Test]`
  2. Visit every caller: if the caller uses the return value, insert a call to the query right before the modifier call (`const found = findMiscreant(people); alertForMiscreant(people);`). `[Test after each caller]`
  3. Remove all `return` values from the modifier function. `[Test]`
  4. Replace duplicated lookup logic inside the modifier with a call to the new query (`7.9 Substitute Algorithm`). `[Test]`

## 11.2 Parameterize Function

- **1st Ed. Aliases**: Parameterize Method
- **Motivation**: Combine two or more functions sharing identical logic with different literal constants (`fivePercentRaise` / `tenPercentRaise`, or tiered usage bands) into one parameterized function, eliminating duplication and making future rate/threshold changes trivial.

```javascript
// Range/Band Parameterization (Ch. 11.2): start from middleBand, use 0 & Infinity for outer bands!
// Before: bottomBand(usage), middleBand(usage), topBand(usage)
function baseCharge(usage) {
  if (usage < 0) return usd(0);
  const amount =
    withinBand(usage, 0, 100) * 0.03 +
    withinBand(usage, 100, 200) * 0.05 +
    withinBand(usage, 200, Infinity) * 0.07;
  return usd(amount);
}
function withinBand(usage, bottom, top) {
  return usage > bottom ? Math.min(usage, top) - bottom : 0;
}
```

- **Mechanics**:
  1. Select the most representative function among the similar siblings (for range bands, pick `middleBand` because it already contains both lower and upper bounds!) and use `6.5 Change Function Declaration` to add the varying literals as parameters. `[Test]`
  2. Replace each literal inside the function body with its new parameter one at a time. `[Test after each]`
  3. Update callers of each sibling function to call the parameterized function with its bounds (`0` for bottom, `Infinity` for unbounded top), then delete the obsolete sibling functions. `[Test after each]`

## 11.3 Remove Flag Argument

- **1st Ed. Aliases**: Replace Parameter with Explicit Methods
- **Motivation**: A *flag argument* is a boolean/enum/string literal passed by callers solely to tell the function *which branch of code to execute* (`deliveryDate(anOrder, true)`). Callers reading `true` at the call site have no idea what `true` means! Explicit functions (`rushDeliveryDate(anOrder)`, `regularDeliveryDate(anOrder)`) make call sites crystal clear.
- **Mixed Callers & Guardrails**:
  - Not a flag argument if **all** callers pass dynamic runtime data (`deliveryDate(anOrder, request.isRushCheckbox)`), or if multiple independent booleans interact across $2^N$ combinations (consider `6.8 Introduce Parameter Object` or polymorphism instead).
  - **Mixed literal + computed callers**: Keep `rushDeliveryDate(order)` and `regularDeliveryDate(order)` for literal callers while retaining `deliveryDate(order, isRush)` only if data-driven callers genuinely exist (if *no* external caller should call the boolean version directly, restrict its visibility or name it `deliveryDateHelperOnly`!).

```javascript
// Before
aShipment.deliveryDate = deliveryDate(anOrder, true);

// After
aShipment.deliveryDate = rushDeliveryDate(anOrder);
```

- **Mechanics**:
  1. **Clean top-level dispatch** (`if (isRush) ... else ...`): apply `10.1 Decompose Conditional` to create explicit functions (`rushDeliveryDate`, `regularDeliveryDate`), update callers passing literals to invoke those explicit functions directly, and delete the flag function. `[Test]`
  2. **Tangled internal flag checks**: create forwarding wrapper functions (`function rushDeliveryDate(anOrder) { return deliveryDate(anOrder, true); }`), migrate literal callers to the explicit wrappers, and hide/rename `deliveryDateHelperOnly`! `[Test]`

## 11.4 Preserve Whole Object

- **Motivation**: Instead of forcing callers to unpack multiple fields from a record (`low = aRoom.daysTempRange.low; high = aRoom.daysTempRange.high; plan.withinRange(low, high)`), pass the whole object (`plan.withinRange(aRoom.daysTempRange)`) or pass `this` when an object passes several of its own properties.
- **When NOT to Use**: Skip if the callee lives in a lower-level module that must **not** depend on the whole host object's type.

```javascript
// Before
const low = aRoom.daysTempRange.low;
const high = aRoom.daysTempRange.high;
if (!aPlan.withinRange(low, high)) ...

// After
if (!aPlan.withinRange(aRoom.daysTempRange)) ...
```

- **Two Safe Mechanics (Ch. 11.4)**:
  - **Mechanics A - Top-Down Wrapper (Default)**:
    1. Create an empty function with the desired whole-object signature under a searchable temporary name (`xxNEWwithinRange(aNumberRange)`).
    2. Fill its body with a delegating call to the old function (`return this.withinRange(aNumberRange.low, aNumberRange.high)`). `[Test]`
    3. Update callers one by one to pass `aRoom.daysTempRange` and delete dead unpacking temps. `[Test after each]`
    4. Apply `6.2 Inline Function` of the old function into `xxNEWwithinRange`, then rename `xxNEWwithinRange` -> `withinRange` (`6.5`). `[Test]`
  - **Mechanics B - Purely Mechanical IDE Composition (Zero Manual Wiring)**:
    1. At a call site, apply `6.3 Extract Variable` on the call result (`const isWithinRange = aPlan.withinRange(low, high);`) and `6.3 Extract Variable` on the whole object (`const tempRange = aRoom.daysTempRange;`). `[Test]`
    2. Apply `6.1 Extract Function` on the unpacking lines + call to produce `xxNEWwithinRange(aPlan, tempRange)`. `[Test]`
    3. Apply `8.1 Move Function` to move `xxNEWwithinRange` onto `HeatingPlan`, then `6.2 Inline Function` + `6.5` rename! `[Test]`

## 11.5 Replace Parameter with Query

- **1st Ed. Aliases**: Replace Parameter with Method | **Inverse**: `11.6 Replace Query with Parameter`
- **Motivation**: Place responsibility for determining a parameter's value inside the callee whenever the callee can cleanly derive it from `this` or existing parameters without adding unwanted dependencies, simplifying every call site.

```javascript
// Before
get finalPrice() {
  const basePrice = this.quantity * this.itemPrice;
  let discountLevel = this.quantity > 100 ? 2 : 1;
  return this.discountedPrice(basePrice, discountLevel);
}

// After: discountLevel derived inside discountedPrice via this.discountLevel getter
get finalPrice() {
  const basePrice = this.quantity * this.itemPrice;
  return this.discountedPrice(basePrice);
}
```

- **Mechanics**:
  1. Extract the parameter computation into a standalone query/getter (`get discountLevel()`) if needed. `[Test]`
  2. Inside the target function body, replace every reference to the parameter with a call to that query. `[Test]`
  3. Apply `6.5 Change Function Declaration` to remove the parameter from declaration and call sites. `[Test]`

## 11.6 Replace Query with Parameter

- **Inverse**: `11.5 Replace Parameter with Query`
- **Motivation**: Achieve **referential transparency** (pure functions returning identical output for identical arguments) and sever undesirable coupling to global state, singletons (`thermostat.selectedTemperature`), or heavyweight domain objects inside a calculation module by pushing the lookup out to callers.

```javascript
// Before: HeatingPlan reaches into global thermostat singleton
get targetTemperature() {
  if (thermostat.selectedTemperature > this._max) return this._max;
  ...
}

// After: pure referentially transparent method
targetTemperature(selectedTemperature) {
  if (selectedTemperature > this._max) return this._max;
  ...
}
```

- **Mechanics**:
  1. Apply `6.3 Extract Variable` inside the function on the global/query expression you want to parameterize (`const selectedTemperature = thermostat.selectedTemperature;`). `[Test]`
  2. Apply `6.1 Extract Function` on the remainder of the body (`xxNEWtargetTemperature(selectedTemperature)`). `[Test]`
  3. Apply `6.4 Inline Variable` on the temp inside the original function. `[Test]`
  4. Apply `6.2 Inline Function` on the original function across callers, then rename `xxNEWtargetTemperature` back to `targetTemperature`. `[Test]`

## 11.7 Remove Setting Method

- **Motivation**: Removing a setter makes immutability intent unambiguous: this field is set strictly during construction and will never mutate afterward.

```javascript
// Before
const martin = new Person();
martin.name = "martin";
martin.id = "1234";

// After: id passed to constructor; set id() removed
const martin = new Person("1234");
martin.name = "martin";
```

- **Mechanics**:
  1. If values are assigned post-construction instead of via constructor arguments, apply `6.5 Change Function Declaration` to add them to the constructor, call the setter inside the constructor, and remove external post-construction setter calls one caller at a time. `[Test]`
  2. Inline the constructor's call to the setter (`this._id = arg`) and delete the setter method. `[Test]`

## 11.8 Replace Constructor with Factory Function

- **Motivation**: Language constructors carry rigid constraints: they must return an instance of the exact named class (never a subclass, delegate-configured variant, Special Case, or pooled instance), cannot have descriptive variant names (`createEngineer(name)`), and require `new` ceremony.

```javascript
// Before
leadEngineer = new Employee(document.leadEngineer, "E");

// After
leadEngineer = createEngineer(document.leadEngineer);
```

- **Mechanics**:
  1. Create a factory function whose body calls `new ClassName(...)` and returns it. `[Test]`
  2. Replace constructor call sites one by one with calls to the factory function (creating specialized named factories like `createEngineer` where literal type codes were passed!). `[Test after each]`
  3. Restrict constructor visibility (`private` / package-scoped) where supported. `[Test]`

## 11.9 Replace Function with Command

- **1st Ed. Aliases**: Replace Method with Method Object | **Inverse**: `11.10 Replace Command with Function`
- **Motivation**: Untangle a massive, complex function packed with interdependent parameters and mutable temps where normal `6.1 Extract Function` fails, or support queuing, undo, and lifecycle customization. Turning the function into a dedicated single-purpose class (`Scorer`) lets parameters and temps live as instance fields shared cleanly across zero-argument private helper methods! *(Note: Fowler chooses plain functions 95% of the time and pulls out Command only when complexity demands it.)*

```javascript
// Before
function score(candidate, medicalExam, scoringGuide) {
  let result = 0; let healthLevel = 0; let highMedicalRiskFlag = false;
  // 80 lines mutating all three locals...
}

// After
function score(candidate, medicalExam, scoringGuide) {
  return new Scorer(candidate, medicalExam, scoringGuide).execute();
}
class Scorer { ... }
```

- **Mechanics**:
  1. Create an empty class named after the function (`Scorer`) and move the function into `execute(...)` on that class, keeping the original function forwarding `return new Scorer().execute(...)`. `[Test]`
  2. Move each parameter of `execute(...)` into the `Scorer` constructor one at a time via `6.5 Change Function Declaration` (`new Scorer(candidate).execute(medicalExam, scoringGuide)`). `[Test after each]`
  3. Convert local variables inside `execute()` into instance fields (`this._result`, `this._healthLevel` - applying `9.1 Split Variable` first if any local was overloaded!), then break `execute()` into small zero-argument methods via `6.1 Extract Function`. `[Test]`

## 11.10 Replace Command with Function

- **Inverse**: `11.9 Replace Function with Command`
- **Motivation**: If a Command Object merely runs one straightforward calculation with no lifecycle state, undo, or thorny decomposition needs, fold it back into a simple function to eliminate class overhead.

```javascript
// Before
class ChargeCalculator {
  constructor(customer, usage, provider) { ... }
  charge() { return this._customer.baseRate * this._usage + this._provider.connectionCharge; }
}

// After
function charge(customer, usage, provider) {
  return customer.baseRate * usage + provider.connectionCharge;
}
```

- **Mechanics**:
  1. Apply `6.1 Extract Function` around `new ChargeCalculator(...).charge()` to create the standalone wrapper function. `[Test]`
  2. Apply `6.2 Inline Function` on any helper methods called inside `charge()` (using `6.3 Extract Variable` first if a helper's return value is referenced multiple times). `[Test]`
  3. Use `6.5 Change Function Declaration` to pass all constructor parameters into `charge(...)` one by one: as you switch `this._customer` -> `customer` inside `charge(...)`, **immediately delete `this._customer = customer` from the constructor** so tests fail loudly if any hidden reference to `this._customer` was missed! `[Test after each field]`
  4. Inline the constructor + `charge(...)` call into the standalone wrapper function, and delete the dead Command class (`8.9 Remove Dead Code`). `[Test]`
