# Master Refactoring Catalog Index (All 61 Canonical Refactorings + 1st-Ed. Map)

Quick-lookup directory corresponding to Chapter 5 (*Introducing the Catalog*) and the official *Refactoring (2nd Edition)* catalog (`https://refactoring.com/catalog/`). Use this index to jump straight to any refactoring by number, name, inverse operation, or 1st-edition (1999) terminology.

## 1. Complete 61-Item Catalog by Chapter

| ID | 2nd Edition Name | Reference File | Inverse Refactoring | 1st Edition (1999) Aliases / Merged Predecessors |
| --- | --- | --- | --- | --- |
| `6.1` | Extract Function | `ch06-first-set.md` | `6.2 Inline Function` | Extract Method |
| `6.2` | Inline Function | `ch06-first-set.md` | `6.1 Extract Function` | Inline Method |
| `6.3` | Extract Variable | `ch06-first-set.md` | `6.4 Inline Variable` | Introduce Explaining Variable |
| `6.4` | Inline Variable | `ch06-first-set.md` | `6.3 Extract Variable` | Inline Temp |
| `6.5` | Change Function Declaration | `ch06-first-set.md` | - | Rename Method, Add Parameter, Remove Parameter |
| `6.6` | Encapsulate Variable | `ch06-first-set.md` | - | Self-Encapsulate Field, Encapsulate Field |
| `6.7` | Rename Variable | `ch06-first-set.md` | - | - |
| `6.8` | Introduce Parameter Object | `ch06-first-set.md` | - | Introduce Parameter Object |
| `6.9` | Combine Functions into Class | `ch06-first-set.md` | - | - |
| `6.10` | Combine Functions into Transform | `ch06-first-set.md` | - | - |
| `6.11` | Split Phase | `ch06-first-set.md` | - | - |
| `7.1` | Encapsulate Record | `ch07-encapsulation.md` | - | Replace Record with Data Class, Replace Array with Object |
| `7.2` | Encapsulate Collection | `ch07-encapsulation.md` | - | Encapsulate Collection |
| `7.3` | Replace Primitive with Object | `ch07-encapsulation.md` | - | Replace Data Value with Object, Replace Type Code with Class |
| `7.4` | Replace Temp with Query | `ch07-encapsulation.md` | - | Replace Temp with Query |
| `7.5` | Extract Class | `ch07-encapsulation.md` | `7.6 Inline Class` | Extract Class |
| `7.6` | Inline Class | `ch07-encapsulation.md` | `7.5 Extract Class` | Inline Class |
| `7.7` | Hide Delegate | `ch07-encapsulation.md` | `7.8 Remove Middle Man` | Hide Delegate |
| `7.8` | Remove Middle Man | `ch07-encapsulation.md` | `7.7 Hide Delegate` | Remove Middle Man |
| `7.9` | Substitute Algorithm | `ch07-encapsulation.md` | - | Substitute Algorithm |
| `8.1` | Move Function | `ch08-moving-features.md` | - | Move Method |
| `8.2` | Move Field | `ch08-moving-features.md` | - | Move Field |
| `8.3` | Move Statements into Function | `ch08-moving-features.md` | `8.4 Move Statements to Callers` | - |
| `8.4` | Move Statements to Callers | `ch08-moving-features.md` | `8.3 Move Statements into Function` | - |
| `8.5` | Replace Inline Code with Function Call | `ch08-moving-features.md` | `6.2 Inline Function` | - |
| `8.6` | Slide Statements | `ch08-moving-features.md` | - | Consolidate Duplicate Conditional Fragments |
| `8.7` | Split Loop | `ch08-moving-features.md` | - | - |
| `8.8` | Replace Loop with Pipeline | `ch08-moving-features.md` | - | - |
| `8.9` | Remove Dead Code | `ch08-moving-features.md` | - | - |
| `9.1` | Split Variable | `ch09-organizing-data.md` | - | Split Temporary Variable, Remove Assignments to Parameters |
| `9.2` | Rename Field | `ch09-organizing-data.md` | - | - |
| `9.3` | Replace Derived Variable with Query | `ch09-organizing-data.md` | - | - |
| `9.4` | Change Reference to Value | `ch09-organizing-data.md` | `9.5 Change Value to Reference` | Change Reference to Value |
| `9.5` | Change Value to Reference | `ch09-organizing-data.md` | `9.4 Change Reference to Value` | Change Value to Reference |
| `10.1` | Decompose Conditional | `ch10-simplifying-conditionals.md` | - | Decompose Conditional |
| `10.2` | Consolidate Conditional Expression | `ch10-simplifying-conditionals.md` | - | Consolidate Conditional Expression |
| `10.3` | Replace Nested Conditional with Guard Clauses | `ch10-simplifying-conditionals.md` | - | Replace Nested Conditional with Guard Clauses |
| `10.4` | Replace Conditional with Polymorphism | `ch10-simplifying-conditionals.md` | - | Replace Conditional with Polymorphism |
| `10.5` | Introduce Special Case | `ch10-simplifying-conditionals.md` | - | Introduce Null Object |
| `10.6` | Introduce Assertion | `ch10-simplifying-conditionals.md` | - | Introduce Assertion |
| `11.1` | Separate Query from Modifier | `ch11-refactoring-apis.md` | - | Separate Query from Modifier |
| `11.2` | Parameterize Function | `ch11-refactoring-apis.md` | - | Parameterize Method |
| `11.3` | Remove Flag Argument | `ch11-refactoring-apis.md` | - | Replace Parameter with Explicit Methods |
| `11.4` | Preserve Whole Object | `ch11-refactoring-apis.md` | - | Preserve Whole Object |
| `11.5` | Replace Parameter with Query | `ch11-refactoring-apis.md` | `11.6 Replace Query with Parameter` | Replace Parameter with Method |
| `11.6` | Replace Query with Parameter | `ch11-refactoring-apis.md` | `11.5 Replace Parameter with Query` | - |
| `11.7` | Remove Setting Method | `ch11-refactoring-apis.md` | - | Remove Setting Method |
| `11.8` | Replace Constructor with Factory Function | `ch11-refactoring-apis.md` | - | Replace Constructor with Factory Method |
| `11.9` | Replace Function with Command | `ch11-refactoring-apis.md` | `11.10 Replace Command with Function` | Replace Method with Method Object |
| `11.10` | Replace Command with Function | `ch11-refactoring-apis.md` | `11.9 Replace Function with Command` | - |
| `12.1` | Pull Up Method | `ch12-dealing-with-inheritance.md` | `12.4 Push Down Method` | Pull Up Method, Form Template Method |
| `12.2` | Pull Up Field | `ch12-dealing-with-inheritance.md` | `12.5 Push Down Field` | Pull Up Field |
| `12.3` | Pull Up Constructor Body | `ch12-dealing-with-inheritance.md` | - | Pull Up Constructor Body |
| `12.4` | Push Down Method | `ch12-dealing-with-inheritance.md` | `12.1 Pull Up Method` | Push Down Method |
| `12.5` | Push Down Field | `ch12-dealing-with-inheritance.md` | `12.2 Pull Up Field` | Push Down Field |
| `12.6` | Replace Type Code with Subclasses | `ch12-dealing-with-inheritance.md` | `12.7 Remove Subclass` | Replace Type Code with Subclasses, Replace Type Code with State/Strategy, Extract Subclass |
| `12.7` | Remove Subclass | `ch12-dealing-with-inheritance.md` | `12.6 Replace Type Code with Subclasses` | Replace Subclass with Fields |
| `12.8` | Extract Superclass | `ch12-dealing-with-inheritance.md` | `12.9 Collapse Hierarchy` | Extract Superclass |
| `12.9` | Collapse Hierarchy | `ch12-dealing-with-inheritance.md` | `12.8 Extract Superclass` | Collapse Hierarchy |
| `12.10` | Replace Subclass with Delegate | `ch12-dealing-with-inheritance.md` | - | Replace Subclass with Delegate, Replace Type Code with State/Strategy |
| `12.11` | Replace Superclass with Delegate | `ch12-dealing-with-inheritance.md` | - | Replace Inheritance with Delegation |

## 2. Alphabetical Lookup (A to S)

- **Change Function Declaration** (`6.5`) -> `ch06-first-set.md`
- **Change Reference to Value** (`9.4`) -> `ch09-organizing-data.md`
- **Change Value to Reference** (`9.5`) -> `ch09-organizing-data.md`
- **Collapse Hierarchy** (`12.9`) -> `ch12-dealing-with-inheritance.md`
- **Combine Functions into Class** (`6.9`) -> `ch06-first-set.md`
- **Combine Functions into Transform** (`6.10`) -> `ch06-first-set.md`
- **Consolidate Conditional Expression** (`10.2`) -> `ch10-simplifying-conditionals.md`
- **Decompose Conditional** (`10.1`) -> `ch10-simplifying-conditionals.md`
- **Encapsulate Collection** (`7.2`) -> `ch07-encapsulation.md`
- **Encapsulate Record** (`7.1`) -> `ch07-encapsulation.md`
- **Encapsulate Variable** (`6.6`) -> `ch06-first-set.md`
- **Extract Class** (`7.5`) -> `ch07-encapsulation.md`
- **Extract Function** (`6.1`) -> `ch06-first-set.md`
- **Extract Superclass** (`12.8`) -> `ch12-dealing-with-inheritance.md`
- **Extract Variable** (`6.3`) -> `ch06-first-set.md`
- **Hide Delegate** (`7.7`) -> `ch07-encapsulation.md`
- **Inline Class** (`7.6`) -> `ch07-encapsulation.md`
- **Inline Function** (`6.2`) -> `ch06-first-set.md`
- **Inline Variable** (`6.4`) -> `ch06-first-set.md`
- **Introduce Assertion** (`10.6`) -> `ch10-simplifying-conditionals.md`
- **Introduce Parameter Object** (`6.8`) -> `ch06-first-set.md`
- **Introduce Special Case** (`10.5`) -> `ch10-simplifying-conditionals.md`
- **Move Field** (`8.2`) -> `ch08-moving-features.md`
- **Move Function** (`8.1`) -> `ch08-moving-features.md`
- **Move Statements into Function** (`8.3`) -> `ch08-moving-features.md`
- **Move Statements to Callers** (`8.4`) -> `ch08-moving-features.md`
- **Parameterize Function** (`11.2`) -> `ch11-refactoring-apis.md`
- **Preserve Whole Object** (`11.4`) -> `ch11-refactoring-apis.md`
- **Pull Up Constructor Body** (`12.3`) -> `ch12-dealing-with-inheritance.md`
- **Pull Up Field** (`12.2`) -> `ch12-dealing-with-inheritance.md`
- **Pull Up Method** (`12.1`) -> `ch12-dealing-with-inheritance.md`
- **Push Down Field** (`12.5`) -> `ch12-dealing-with-inheritance.md`
- **Push Down Method** (`12.4`) -> `ch12-dealing-with-inheritance.md`
- **Remove Dead Code** (`8.9`) -> `ch08-moving-features.md`
- **Remove Flag Argument** (`11.3`) -> `ch11-refactoring-apis.md`
- **Remove Middle Man** (`7.8`) -> `ch07-encapsulation.md`
- **Remove Setting Method** (`11.7`) -> `ch11-refactoring-apis.md`
- **Remove Subclass** (`12.7`) -> `ch12-dealing-with-inheritance.md`
- **Rename Field** (`9.2`) -> `ch09-organizing-data.md`
- **Rename Variable** (`6.7`) -> `ch06-first-set.md`
- **Replace Command with Function** (`11.10`) -> `ch11-refactoring-apis.md`
- **Replace Conditional with Polymorphism** (`10.4`) -> `ch10-simplifying-conditionals.md`
- **Replace Constructor with Factory Function** (`11.8`) -> `ch11-refactoring-apis.md`
- **Replace Derived Variable with Query** (`9.3`) -> `ch09-organizing-data.md`
- **Replace Function with Command** (`11.9`) -> `ch11-refactoring-apis.md`
- **Replace Inline Code with Function Call** (`8.5`) -> `ch08-moving-features.md`
- **Replace Loop with Pipeline** (`8.8`) -> `ch08-moving-features.md`
- **Replace Nested Conditional with Guard Clauses** (`10.3`) -> `ch10-simplifying-conditionals.md`
- **Replace Parameter with Query** (`11.5`) -> `ch11-refactoring-apis.md`
- **Replace Primitive with Object** (`7.3`) -> `ch07-encapsulation.md`
- **Replace Query with Parameter** (`11.6`) -> `ch11-refactoring-apis.md`
- **Replace Subclass with Delegate** (`12.10`) -> `ch12-dealing-with-inheritance.md`
- **Replace Superclass with Delegate** (`12.11`) -> `ch12-dealing-with-inheritance.md`
- **Replace Temp with Query** (`7.4`) -> `ch07-encapsulation.md`
- **Replace Type Code with Subclasses** (`12.6`) -> `ch12-dealing-with-inheritance.md`
- **Separate Query from Modifier** (`11.1`) -> `ch11-refactoring-apis.md`
- **Slide Statements** (`8.6`) -> `ch08-moving-features.md`
- **Split Loop** (`8.7`) -> `ch08-moving-features.md`
- **Split Phase** (`6.11`) -> `ch06-first-set.md`
- **Split Variable** (`9.1`) -> `ch09-organizing-data.md`
- **Substitute Algorithm** (`7.9`) -> `ch07-encapsulation.md`

## 3. Where 1st-Edition Classics Moved in 2nd Edition

- **Replace Array with Object** -> `7.1 Encapsulate Record` (treat positional tuples like `["Liverpool", 15]` as records with named getters).
- **Replace Magic Number with Symbolic Constant** -> `6.3 Extract Variable` / `6.7 Rename Variable` at module/constant scope.
- **Change Unidirectional Association to Bidirectional** (and inverse) -> `8.2 Move Field` + encapsulating updates inside the owning setter (`6.6 Encapsulate Variable`).
- **Consolidate Duplicate Conditional Fragments** -> `8.6 Slide Statements` across `if/else` boundaries.
- **Remove Control Flag** -> `10.3 Replace Nested Conditional with Guard Clauses` (`return` / `break`) or `6.1 Extract Function`.
- **Replace Type Code with State/Strategy** -> `12.6 Replace Type Code with Subclasses` (indirect `EmployeeType` wrapper) or `12.10 Replace Subclass with Delegate`.
- **Form Template Method** -> `6.1 Extract Function` on varying steps to make outlines identical, followed by `12.1 Pull Up Method`.
- **Introduce Foreign Method / Introduce Local Extension** -> `6.9 Combine Functions into Class`, `6.10 Combine Functions into Transform`, or module-level utility functions (`8.1 Move Function`).
- **Big-Picture ("Tease Apart Inheritance", "Convert Procedural Design to Objects", "Separate Domain from Presentation", "Extract Hierarchy")** -> Composed via `6.11 Split Phase`, `12.10 Replace Subclass with Delegate`, and the multi-move pipelines in `references/playbooks-and-compositions.md`.
