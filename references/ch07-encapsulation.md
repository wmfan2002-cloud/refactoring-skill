# Chapter 7: Encapsulation (9 Items)

Parnas's modularization rule: hide each module's secrets (mutable records, collections, primitives, temps, collaborates, and internal algorithms) behind clean boundaries. Run static checks and tests at every `[Test]` checkpoint.

## 7.1 Encapsulate Record

- **1st Ed. Aliases**: Replace Record with Data Class
- **Motivation**: Replace mutable naked records, dictionaries, or nested JSON maps with a class so stored vs. derived values are indistinguishable, field names are explicit, and updates pass through controlled methods. *(Immutable records do not need this; enrich them via `6.10 Combine Functions into Transform` instead.)*

```javascript
// Before
const organization = { name: "Acme Gooseberries", country: "GB" };
organization.name = newName;

// After
class Organization {
  constructor(data) { this._name = data.name; this._country = data.country; }
  get name() { return this._name; }
  set name(aString) { this._name = aString; }
  get country() { return this._country; }
}
```

- **Mechanics**:
  1. Apply `6.6 Encapsulate Variable` on the variable holding the record using an intentionally ugly, searchable name (`getRawDataOfOrganization()`). `[Test]`
  2. Create a class wrapping the raw record (`this._data = data`), expose a temporary raw getter on it, instantiate the class, and add a clean getter (`getOrganization()`) returning the class instance. `[Test]`
  3. **Migrate all write/mutation sites first**: replace direct field/nested writes (`raw[id].usages[y][m] = v`) with explicit setter/mutator methods (`setUsage(id, y, m, v)`) on the class. `[Test after each]`
  4. Verify zero remaining hidden mutations by making `rawData` return a deep clone (`structuredClone`) or frozen proxy and running tests! `[Test]`
  5. Migrate read sites to getters (or `rawData` deep-copy / nested `Encapsulate Record` for complex read trees), delete `getRawDataOf...`, and unpack flat `_data` into private fields. `[Test]`

## 7.2 Encapsulate Collection

- **Motivation**: Prevent a classic encapsulation leak where `person.courses` has a getter, yet callers mutate the underlying array directly (`person.courses.push(c)` or in-place `.sort()`) without the owning `Person` class knowing.

```javascript
// Before
class Person {
  get courses() { return this._courses; }
  set courses(aList) { this._courses = aList; }
}

// After
class Person {
  get courses() { return this._courses.slice(); }
  addCourse(aCourse) { this._courses.push(aCourse); }
  removeCourse(aCourse) { ... }
}
```

- **Mechanics**:
  1. Apply `6.6 Encapsulate Variable` if the collection field is not yet behind accessors.
  2. Add `addX(item)` and `removeX(item)` domain mutators to the host class.
  3. Remove any raw collection setter via `11.7 Remove Setting Method` (or if required, store a defensive copy `this._courses = aList.slice()`).
  4. Find all callers mutating the returned collection directly and convert them to call `addX` / `removeX`. `[Test]`
  5. Change the collection getter to return a shallow copy (`slice()`, `[...list]`, `List.copyOf`) or read-only view so collection pipelines still work cleanly while external mutation becomes impossible. `[Test]`

## 7.3 Replace Primitive with Object

- **1st Ed. Aliases**: Replace Data Value with Object, Replace Type Code with Class
- **Motivation**: Graduate a raw string or number (`priority`, `telephone`, `money`, `currency`) into a dedicated domain class as soon as validation, formatting, parsing, or comparison logic appears beyond simple printing.

```javascript
// Before
orders.filter(o => "high" === o.priority || "rush" === o.priority);

// After
orders.filter(o => o.priority.higherThan(new Priority("normal")));
```

- **Mechanics**:
  1. Apply `6.6 Encapsulate Variable` on the primitive field. `[Test]`
  2. Create a simple wrapper class (`Priority`) storing the value with a `toString()` or value getter.
  3. Change the host setter to instantiate `new Priority(arg)` and the getter (`priorityString`) to return `this._priority.toString()`. `[Test]`
  4. Add a rich getter (`get priority() { return this._priority; }`), make the constructor idempotent (`if (val instanceof Priority) return val;`), and apply `9.4 Change Reference to Value` (`equals()`, `higherThan()`, validation) so domain behavior moves onto the new Value Object. `[Test]`

## 7.4 Replace Temp with Query

- **Motivation**: Eliminate derived local variables inside classes/modules before `6.1 Extract Function` so extracted methods read `this.basePrice` directly instead of requiring long parameter lists.
- **Precondition**: Apply **only** to deterministic, single-calculation temps whose expression yields the same answer whenever called (never snapshot temps like `const oldPrice = item.price` before mutating `item`!).

```javascript
// Before
get price() {
  const basePrice = this._quantity * this._itemPrice;
  return basePrice > 1000 ? basePrice * 0.95 : basePrice * 0.98;
}

// After
get price() {
  return this.basePrice > 1000 ? this.basePrice * 0.95 : this.basePrice * 0.98;
}
get basePrice() { return this._quantity * this._itemPrice; }
```

- **Mechanics**:
  1. Ensure the temp is completely calculated before use; mark it `const` / `final` and `[Test]` (if conditionally adjusted in two lines right at initialization, extract both lines together).
  2. Extract the assignment right-hand side into a pure query method (if impure, run `11.1 Separate Query from Modifier` first). `[Test]`
  3. Apply `6.4 Inline Variable` to remove the temp. `[Test]`

## 7.5 Extract Class

- **Inverse**: `7.6 Inline Class`
- **Motivation**: Split a class that has accumulated multiple responsibilities, prefixed field groups (`officeAreaCode`, `officeNumber`), or independent reasons to change into crisp collaborating classes.

```javascript
// Before: Person manages both identity and office phone formatting
class Person { get officeAreaCode() {...} get officeNumber() {...} get telephoneNumber() {...} }

// After: Person delegates phone responsibilities to TelephoneNumber
class Person {
  constructor() { this._telephoneNumber = new TelephoneNumber(); }
  get officeNumber() { return this._telephoneNumber.number; }
  get telephoneNumber() { return this._telephoneNumber.toString(); }
}
```

- **Mechanics**:
  1. Decide how to partition the class's responsibilities and create the new child class (`TelephoneNumber`).
  2. Instantiate the child class inside the parent constructor (`this._telephoneNumber = new TelephoneNumber()`).
  3. Move each belonging field one at a time via `8.2 Move Field`. `[Test after each]`
  4. Move belonging methods from lowest-level callees upward via `8.1 Move Function`. `[Test after each]`
  5. Review both interfaces: strip contextual prefixes (`officeAreaCode` -> `areaCode` inside `TelephoneNumber`), trim unneeded wrappers, and apply `9.4 Change Reference to Value` if exposing the new class as a Value Object. `[Test]`

## 7.6 Inline Class

- **Inverse**: `7.5 Extract Class`
- **Motivation**: Fold anemic classes that no longer justify their existence back into their primary host, or merge two awkward classes into one before re-splitting cleanly via `7.5 Extract Class`.

```javascript
// Before: Shipment delegates everything to a trivial TrackingInformation wrapper
// After: trackingCompany and trackingNumber fields live directly on Shipment
```

- **Mechanics**:
  1. On the target host class, create delegating methods for every public method of the source class.
  2. Update all external callers to call the target class's methods instead of accessing the source class. `[Test]`
  3. Move all methods and fields from the source class into the target class one by one (`6.2 Inline Function` / `8.2 Move Field`). `[Test]`
  4. Delete the empty source class. `[Test]`

## 7.7 Hide Delegate

- **Inverse**: `7.8 Remove Middle Man`
- **Motivation**: Shield clients from structural navigation chains (`aPerson.department.manager`) so changes to how `Person` tracks its manager do not ripple out to callers.

```javascript
// Before
manager = aPerson.department.manager;

// After
manager = aPerson.manager; // class Person { get manager() { return this._department.manager; } }
```

- **Mechanics**:
  1. For each delegate method needed by clients, create a simple delegating method on the server class.
  2. Adjust callers to invoke the server's delegating method instead of traversing the delegate. `[Test after each]`
  3. If no external caller needs the delegate accessor anymore, remove the delegate getter from the server. `[Test]`

## 7.8 Remove Middle Man

- **Inverse**: `7.7 Hide Delegate`
- **Motivation**: Cure *Middle Man* bloat (often caused by dogmatic Law of Demeter wrappers) when every new feature on a delegate forces you to add yet another pass-through method on the server class.

```javascript
// Before
manager = aPerson.manager; // Person has 10 one-line getters forwarding to this._department

// After
manager = aPerson.department.manager;
```

- **Mechanics**:
  1. Create a getter on the server class returning the delegate object (`get department()`).
  2. Update callers of pass-through methods to call through `aPerson.department` directly (or encapsulate `_department` and apply `6.2 Inline Function` on the pass-through methods). `[Test]`
  3. Remove the pass-through methods (retaining a few high-frequency convenience methods is fine if pragmatic). `[Test]`

## 7.9 Substitute Algorithm

- **Motivation**: Replace a tangled custom algorithm wholesale with a far simpler algorithm or standard library pipeline once the problem is clearly understood.

```javascript
// Before
function foundPerson(people) {
  for (let i = 0; i < people.length; i++) {
    if (people[i] === "Don") return "Don";
    if (people[i] === "John") return "John";
  }
  return "";
}

// After
function foundPerson(people) {
  const candidates = ["Don", "John"];
  return people.find(p => candidates.includes(p)) || "";
}
```

- **Mechanics**:
  1. Factor the target algorithm completely into a single standalone function (`6.1 Extract Function`) so boundaries are crisp.
  2. Lock down behavior with comprehensive unit and edge-case tests on that function alone. `[Test]`
  3. Prepare the replacement algorithm and swap it in.
  4. Run static checks and tests; if any test fails, run the old and new functions side by side on failing test inputs to isolate the exact behavioral discrepancy. `[Test]`
