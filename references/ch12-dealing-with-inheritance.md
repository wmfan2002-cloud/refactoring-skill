# Chapter 12: Dealing with Inheritance (11 Items)

Inheritance is powerful and famously easy to misuse. Use these 11 refactorings to move members up and down valid hierarchies, introduce/remove subclasses around type codes, extract or collapse hierarchy layers, and - most importantly - **replace brittle inheritance with delegation** whenever categories change over time, orthogonal variation axes collide, or subclasses violate Liskov substitutability. Run static checks and tests at every `[Test]` checkpoint.

## 12.1 Pull Up Method

- **1st Ed. Aliases**: Pull Up Method, Form Template Method | **Inverse**: `12.4 Push Down Method`
- **Motivation**: Eliminate duplicated methods across sibling subclasses before one copy gets updated and the other becomes a bug.

```javascript
// Before: Employee and Department both define identical get annualCost() { return this.monthlyCost * 12; }
// After: annualCost pulled up onto Party superclass (declaring trap get monthlyCost() { throw new SubclassResponsibilityError(); } on Party)
```

- **Mechanics**:
  1. Inspect all candidate methods across subclasses; if workflows match in outline but differ in details (*Form Template Method*), apply `6.1 Extract Function` on the differing steps with identical hook names across subclasses until the outer method bodies are character-for-character identical! `[Test]`
  2. Check that every method and field referenced inside the body is accessible on the superclass (`12.2 Pull Up Field` or add an abstract/trap method `throw new SubclassResponsibilityError()` on the superclass in dynamic languages).
  3. Apply `6.5 Change Function Declaration` if method signatures differ.
  4. Copy the method onto the superclass, delete it from one subclass `[Test]`, then delete from each remaining subclass one by one `[Test]`.

## 12.2 Pull Up Field

- **Inverse**: `12.5 Push Down Field`
- **Motivation**: Merge duplicate fields across subclasses into the superclass to deduplicate data declarations and unlock `12.1 Pull Up Method` and `12.3 Pull Up Constructor Body`.

- **Mechanics**:
  1. Inspect all uses of the candidate fields to confirm they are used identically.
  2. Rename fields via `9.2 Rename Field` if their names differ across subclasses.
  3. Create the `protected` (or superclass-encapsulated) field on the superclass and delete the subclass field declarations. `[Test]`

## 12.3 Pull Up Constructor Body

- **Motivation**: Constructors do not inherit cleanly like normal methods; factor duplicated `this._name = name` initialization up into `super(name)` (and extract post-`super()` common setup into a shared superclass helper method!).

```javascript
// Before
class Employee extends Party { constructor(name, id, monthlyCost) { super(); this._id = id; this._name = name; ... } }

// After
class Party { constructor(name) { this._name = name; } }
class Employee extends Party { constructor(name, id, monthlyCost) { super(name); this._id = id; ... } }
```

- **Mechanics**:
  1. Define a superclass constructor if missing and ensure subclasses call `super()`.
  2. Use `8.6 Slide Statements` to move common assignment statements right after `super()`. `[Test]`
  3. Move the common code into the superclass constructor (passing needed constructor arguments into `super(...)`). `[Test]`
  4. **Post-subclass initialization variant**: If shared initialization code (`if (this.isPrivileged) this.assignCar();`) depends on subclass fields (`this._grade = grade`) set *after* `super()`, apply `6.1 Extract Function` (`finishConstruction()`) and `12.1 Pull Up Method` onto the superclass! `[Test]`

## 12.4 Push Down Method

- **Inverse**: `12.1 Pull Up Method`
- **Motivation**: Move a method from a superclass down into the specific subclass(es) that actually use it, decluttering the base class. *(Precondition: callers know the concrete subtype! If callers invoke polymorphically without knowing subtype, use `10.4 Replace Conditional with Polymorphism` with a benign base default instead.)*

- **Mechanics**:
  1. Copy the method into every subclass (or every subclass that uses it).
  2. Remove it from the superclass. `[Test]`
  3. Remove it from each unneeded subclass one by one. `[Test after each]`

## 12.5 Push Down Field

- **Inverse**: `12.2 Pull Up Field`
- **Motivation**: Move a field worked with by only one or a small subset of subclasses down out of the superclass.

- **Mechanics**:
  1. Declare the field in every subclass that needs it.
  2. Remove it from the superclass. `[Test]`

## 12.6 Replace Type Code with Subclasses

- **1st Ed. Aliases**: Extract Subclass, Replace Type Code with State/Strategy | **Inverse**: `12.7 Remove Subclass`
- **Motivation**: Enable `10.4 Replace Conditional with Polymorphism` and `12.5 Push Down Field` when behavior or valid fields depend on a type code (`"engineer"`, `"manager"`, `"salesman"`).
- **Direct vs. Indirect Subclassing**:
  - *Direct (`Engineer extends Employee`)*: Simple when type is immutable and `Employee` has no competing inheritance axis.
  - *Indirect (`Engineer extends EmployeeType` property on `Employee`)*: Apply `7.3 Replace Primitive with Object` on `_type` first, then apply `12.6` to `Employee.createEmployeeType(aString)`! Preserves `Employee`'s own hierarchy (e.g., `FullTimeEmployee` / `PartTimeEmployee`) AND permits changing an employee's type dynamically via `set type(arg)`!

```javascript
// Variant A: Direct factory + subclass pattern
function createEmployee(name, type) {
  switch (type) {
    case "engineer": return new Engineer(name);
    case "salesman": return new Salesman(name);
    case "manager": return new Manager(name);
    default: throw new Error(`Employee cannot be of type ${type}`);
  }
}

// Variant B: Indirect EmployeeType property hierarchy (supports mutable type & orthogonal subclasses)
class EmployeeType { get capitalizedName() { ... } }
class Engineer extends EmployeeType { toString() { return "engineer"; } }
class Employee {
  set type(arg) { this._type = Employee.createEmployeeType(arg); }
}
```

- **Mechanics**:
  1. Self-encapsulate the type code field (`6.6 Encapsulate Variable`).
  2. Choose direct subclassing vs. wrapping the type code in a helper object (`7.3 Replace Primitive with Object`) first.
  3. Apply `11.8 Replace Constructor with Factory Function` to wrap instantiation. `[Test]`
  4. For one type code value at a time: create its subclass overriding the type-code getter, add its selector case in the factory, `[Test]`, and **perform a quick fault-injection check** (temporarily return `"bogus"` from `Engineer.type` to confirm tests turn red and prove the factory actually routes to `Engineer`, then revert!).
  5. Move type validation (`validateType`) into the factory's `default:` branch, and remove the type-code field and constructor parameter once all valid cases dispatch to subclasses. `[Test]`

## 12.7 Remove Subclass

- **1st Ed. Aliases**: Replace Subclass with Fields | **Inverse**: `12.6 Replace Type Code with Subclasses`
- **Motivation**: A subclass that does too little (e.g., `Male extends Person` / `Female extends Person` returning only `"M"` / `"F"`) costs cognitive overhead without paying rent; replace it with a simple field on the superclass.

- **Mechanics**:
  1. Wrap subclass constructors behind `11.8 Replace Constructor with Factory Function` (extracting any client data-loading `switch (record.gender)` directly into `createPerson(aRecord)`). `[Test]`
  2. If any caller tests `p instanceof Male`, use `6.1 Extract Function` + `8.1 Move Function` to turn that check into a superclass predicate (`get isMale() { return "M" === this._genderCode; }`). `[Test]`
  3. Create a field on the superclass (`this._genderCode = genderCode || "X"`) representing the distinction symmetrically across constructor and factory.
  4. Change one subclass case at a time in the factory to instantiate `new Person(name, "M")`, delete `Male`, `[Test]`, and repeat for remaining subclasses!

## 12.8 Extract Superclass

- **Inverse**: `12.9 Collapse Hierarchy`
- **Motivation**: When two independent classes (`Employee` and `Department`) turn out to share parallel concepts (names, monthly/annual cost math), pull those commonalities up into a new shared superclass (`Party`) once the overlap is concrete (choose `7.5 Extract Class` via delegation instead if subtype substitutability does not fit).

- **Mechanics**:
  1. Create an empty superclass (`Party`) and make the original classes inherit from it. `[Test]`
  2. One by one, apply `12.2 Pull Up Field` and `12.3 Pull Up Constructor Body` to move shared state up. `[Test]`
  3. Apply `12.1 Pull Up Method` to move shared behavior up (using `6.5 Change Function Declaration` first if method names like `totalMonthlyCost` vs. `monthlyCost` need alignment). `[Test]`
  4. Check clients to see if type references can be generalized to the superclass.

## 12.9 Collapse Hierarchy

- **Inverse**: `12.8 Extract Superclass`
- **Motivation**: Merge a superclass and subclass into a single class when refactoring has stripped away any meaningful difference between them.

- **Mechanics**:
  1. Pick one class to survive (whichever name makes more domain sense now).
  2. Move all fields and methods into the survivor via `12.1`/`12.2` Pull Up or `12.4`/`12.5` Push Down. `[Test]`
  3. Update all references to the Victim class to point to the Survivor class, and delete the empty Victim class. `[Test]`

## 12.10 Replace Subclass with Delegate

- **Motivation**: Inheritance has two severe structural limitations:
  1. **Single variation axis**: If `Booking` or `Bird` already needs subclasses along another axis (`WildBird` vs. `CaptiveBird`), you cannot subclass again by species.
  2. **Fixed for object lifetime**: Converting a regular booking into a premium booking in place (`aBooking._bePremium(extras)`) fails with static subclasses, and subclass overrides couple tightly to superclass internals.
  Delegation solves both cleanly! *(Prefer simple subclasses first when neither limitation applies, then refactor to a delegate whenever needed.)*

```javascript
// 1. Avoiding infinite recursion when subclass called super.basePrice (two safe patterns):
// Pattern A: _privateBasePrice on host  |  Pattern B: delegate.extendBasePrice(result)
class Booking {
  get basePrice() {
    let result = this._show.price;
    if (this.isPeakDay) result += Math.round(result * 0.15);
    return this._premiumDelegate ? this._premiumDelegate.extendBasePrice(result) : result;
  }
  get hasDinner() { return this._premiumDelegate ? this._premiumDelegate.hasDinner : undefined; }
}

// 2. Replacing an ENTIRE hierarchy (Bird -> SpeciesDelegate superclass):
class Bird {
  constructor(data) {
    this._name = data.name;
    this._speciesDelegate = this.selectSpeciesDelegate(data); // defaults to new SpeciesDelegate(data, this)
  }
  get plumage() { return this._speciesDelegate.plumage; } // zero if-guards!
}
```

- **Key Traps & Full-Hierarchy Composition (Ch. 12.10)**:
  - **Infinite `super` Recursion Trap**: When `PremiumBooking.basePrice` called `super.basePrice`, moving it onto `PremiumBookingDelegate` and calling `this._host.basePrice` loops forever! Either extract `_privateBasePrice` on `Booking` for the delegate to call, OR compute the base price on `Booking` and pass it into `this._premiumDelegate.extendBasePrice(result)`.
  - **Subclass-Only Methods**: When moving a method that existed *only* on `PremiumBooking` (`hasDinner`), add a guard accessor on `Booking` returning `undefined` (or throwing an explicit domain error) when `_premiumDelegate` is absent.
  - **Replacing a Multi-Subclass Hierarchy (`Bird` -> `SpeciesDelegate`)**: Rather than writing `if (this._speciesDelegate)` in every `Bird` method, apply `12.8 Extract Superclass` across the species delegates (`EuropeanSwallowDelegate`, `AfricanSwallowDelegate`, ...) to create a default `SpeciesDelegate(data, bird)` base class! That combines **composition** on `Bird` (freeing `Bird` to subclass into `WildBird`/`CaptiveBird`) with **inheritance** inside `SpeciesDelegate` to share default bird rules cleanly.
- **Mechanics**:
  1. Wrap constructors behind `11.8 Replace Constructor with Factory Function`. `[Test]`
  2. Create a delegate class accepting a `host` back-reference plus subclass-specific data.
  3. Add a delegate field on the superclass and attach it inside the factory (or `selectSpeciesDelegate`). `[Test]`
  4. Move each subclass override onto the delegate (`8.1 Move Function`), add host dispatch, and delete the subclass override! `[Test after each]`
  5. Move subclass fields onto the delegate (`8.2 Move Field`), return the configured host directly from the factory, and delete the empty subclass(es)! `[Test]`

## 12.11 Replace Superclass with Delegate

- **1st Ed. Aliases**: Replace Inheritance with Delegation
- **Motivation**: Cure broken "inheritance for code reuse" (`Stack extends List` exposing bogus `.get(3)` / `.clear()` methods) and the classic **Type-Instance Homonym** modeling error (`Car extends CarModel`, or physical copy `Scroll extends CatalogItem` confusing an individual physical scroll's cleaning date and ID with shared catalog metadata!). True subtyping requires every instance of the subtype to be a valid substitutable instance of the supertype.

```javascript
// Before: physical Scroll wrongly inherits from CatalogItem (conflating copy id with catalog id!)
class Scroll extends CatalogItem { constructor(id, title, tags, dateLastCleaned) { super(id, title, tags); ... } }

// After (12.11 + 9.5 Change Value to Reference):
class Scroll {
  constructor(id, dateLastCleaned, catalogID, catalog) {
    this._id = id;
    this._catalogItem = catalog.get(catalogID);
    this._lastCleaned = dateLastCleaned;
  }
  get id() { return this._id; }
  get title() { return this._catalogItem.title; }
  hasTag(aString) { return this._catalogItem.hasTag(aString); }
}
```

- **Mechanics**:
  1. Create a field on the subclass (`this._catalogItem`) initialized in the subclass constructor to `new Superclass(...)` (if splitting a conflated ID like `Scroll.id` vs. `CatalogItem.id`, store `this._id = id` on `Scroll` and pass `null` temporarily to `new CatalogItem(null, title, tags)` so callers of `CatalogItem.id` are exposed!).
  2. For every superclass element legitimately part of the subclass's interface, create forwarding methods on the subclass delegating to `this._catalogItem` (migrate getter/setter pairs together before testing). `[Test]`
  3. Delete `extends Superclass` and `super(...)`! `[Test]`
  4. **Follow-up Check**: If multiple instances should share one canonical target (`CatalogItem`), chain straight into `9.5 Change Value to Reference` (`this._catalogItem = catalog.get(catalogID)`)! `[Test]`
