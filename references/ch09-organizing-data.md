# Chapter 9: Organizing Data (5 Items)

Giving every variable a single immutable purpose, keeping field names sharp, eliminating redundant mutable derived state, and choosing cleanly between immutable Value Objects and shared Reference Entities. Run static checks and tests at every `[Test]` checkpoint.

## 9.1 Split Variable

- **1st Ed. Aliases**: Remove Assignments to Parameters, Split Temp
- **Motivation**: Outside of loop counters (`i++`) and collecting variables (`sum += x`), every variable should store **one thing** and be declared `const` / `final`. Reusing one variable (or reassigning an input parameter) for two meanings confuses readers and breaks `6.1 Extract Function`.

```javascript
// Before
let temp = 2 * (height + width);
console.log(temp);
temp = height * width;
console.log(temp);

// After
const perimeter = 2 * (height + width);
console.log(perimeter);
const area = height * width;
console.log(area);
```

- **Mechanics**:
  1. Check it is not a genuine *collecting variable* (`acc = acc + next`). If splitting a reassigned input parameter (`function discount(inputValue)`), insert `let result = inputValue;` at the top first.
  2. Change the variable's name at its declaration/first assignment to capture its first meaning, and mark it `const` / `final`.
  3. Update all references between the first and second assignments to use the new name, and declare the variable freshly at the second assignment. `[Test]`
  4. Repeat for each subsequent assignment until every variable is assigned once and marked immutable. `[Test]`

## 9.2 Rename Field

- **Motivation**: Data structures explain more about a program than flowcharts ever will (Fred Brooks). Evolve record keys and class property accessors promptly as domain vocabulary sharpens.

```javascript
// Before
const organization = { name: "Acme Gooseberries", country: "GB" };

// After (encapsulated or immutable record with field renamed name -> title)
class Organization { get title() { return this._title; } set title(s) { this._title = s; } ... }
```

- **Mechanics**:
  1. **Narrow local/immutable scope**: rename all field reads/writes in one pass (or copy `newField = oldField` on immutable records and migrate readers incrementally). `[Test]`
  2. **Widely used mutable record**: apply `7.1 Encapsulate Record` first so data sits behind a class! `[Test]`
  3. Rename the internal private field (`this._title`), updating constructor and existing `get name()` / `set name()` to use `this._title`. `[Test]`
  4. Update the constructor to accept **both** keys (`this._title = data.title !== undefined ? data.title : data.name`), migrate constructor callers to pass `title`, then remove `data.name` fallback. `[Test]`
  5. Rename the getter and setter using `6.5 Change Function Declaration`. `[Test]`

## 9.3 Replace Derived Variable with Query

- **Motivation**: Mutable data is a top source of coupling bugs; mutable data that can easily be computed from other fields (`this._production` manually incremented alongside `this._adjustments.push(a)`) is **duplicated data** waiting to drift out of sync!

```javascript
// Before
get production() { return this._production; }
applyAdjustment(anAdjustment) {
  this._adjustments.push(anAdjustment);
  this._production += anAdjustment.amount;
}

// After
get production() { return this._adjustments.reduce((sum, a) => sum + a.amount, 0); }
applyAdjustment(anAdjustment) { this._adjustments.push(anAdjustment); }
```

- **Mechanics**:
  1. Find all update points for the derived variable. **Multiple data sources trap**: if initialized with a non-zero seed (`constructor(production)`), apply `9.1 Split Variable` first to separate immutable `this._initialProduction` from mutable `this._productionAccumulator = 0`! `[Test]`
  2. Write a side-effect-free query (`get calculatedProduction()`) computing the value from authoritative source data.
  3. Use `10.6 Introduce Assertion` inside the getter (`assert(this._production === this.calculatedProduction)`) and run tests to prove equivalence across every scenario! `[Test]`
  4. Change the getter to return the query result directly (and inline the helper if clean). `[Test]`
  5. Apply `8.9 Remove Dead Code` to delete the backing variable and every incremental update line. `[Test]`

## 9.4 Change Reference to Value

- **Inverse**: `9.5 Change Value to Reference`
- **Motivation**: Convert an embedded mutable object (`_telephoneNumber`, `_price`) into an immutable **Value Object** where updates replace the whole instance (`new Money(...)`) rather than mutating interior properties in place. Value Objects eliminate aliasing bugs and are safe to pass anywhere.
- **When NOT to Use**: Do not apply if multiple holders intentionally share the inner object so mutations in one place propagate live to the others!

```javascript
// Before: mutating inner object in place
class Person { set officeAreaCode(arg) { this._telephoneNumber.areaCode = arg; } }

// After: immutable Value Object with value-based equals()
class Person {
  set officeAreaCode(arg) {
    this._telephoneNumber = new TelephoneNumber(arg, this.officeNumber);
  }
}
```

- **Mechanics**:
  1. Verify the candidate class can be made completely immutable.
  2. Add all fields to its constructor (`6.5 Change Function Declaration`) and apply `11.7 Remove Setting Method` to delete every setter, updating host mutators to assign a brand-new `new ValueClass(...)` instance. `[Test after each setter]`
  3. Implement **value-based equality** (`equals(other)` + `hashCode()` in languages with hash collections) comparing all constituent fields, and write unit tests asserting two separately constructed instances with identical values compare equal (and non-equal against `null` / different values). `[Test]`

## 9.5 Change Value to Reference

- **Inverse**: `9.4 Change Reference to Value`
- **Motivation**: When 5 `Order` instances each construct their own `new Customer(data.customerId)`, updating that customer's credit limit or address in one order leaves the other 4 copies stale and inconsistent. Switch to a single shared **Reference Entity** fetched from a repository.

```javascript
// Before
this._customer = new Customer(data.customer);

// After
this._customer = customerRepository.registerCustomer(data.customer);
```

- **Mechanics**:
  1. Create a repository / identity map (`Map<id, Entity>`) if one does not already exist (pass/inject the repository rather than hardcoding globals where practical).
  2. Ensure the host constructor has the entity's unique identifier and access to the repository.
  3. Modify host constructors to fetch/register the canonical instance from the repository instead of calling `new Entity(...)`. `[Test]`
