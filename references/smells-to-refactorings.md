# Bad Smells in Code: Diagnostic & Refactoring Matrix (Chapter 3)

Fowler and Beck emphasize that *no rigid numeric threshold substitutes for informed human intuition*: a smell is a surface cue telling you where to look, not a blind law. In the 2nd Edition (2018), Fowler and Beck overhauled the catalog to **24 smells** (adding *Mysterious Name*, *Global Data*, *Mutable Data*, and *Loops*; renaming *Long Method -> Long Function*, *Lazy Class -> Lazy Element*, *Switch Statements -> Repeated Switches*, and *Inappropriate Intimacy -> Insider Trading*; and folding *Parallel Inheritance Hierarchies* and *Incomplete Library Class* into broader guidance).

## Master 24-Smell Quick-Lookup Cheat Sheet

| # | Bad Smell | Primary Catalog Remedies | Key Legitimate Exception / Guardrail |
| --- | --- | --- | --- |
| 1 | **Mysterious Name** | `6.5 Change Function Declaration`, `6.7 Rename Variable`, `9.2 Rename Field` | If naming stays hard, split responsibilities first (`6.1`, `6.11`) |
| 2 | **Duplicated Code** | `6.1 Extract Function`, `8.6 Slide Statements`, `12.1 Pull Up Method`, `11.2 Parameterize Function` | Verify structural similarity is not accidental (`8.5` domain-intent test) |
| 3 | **Long Function** | `6.1 Extract Function`, `7.4 Replace Temp with Query`, `6.11 Split Phase`, `11.9 Replace Function with Command` | Even 1 line warrants extraction if intent differs from implementation |
| 4 | **Long Parameter List** | `11.5 Replace Parameter with Query`, `11.4 Preserve Whole Object`, `6.8 Introduce Parameter Object`, `11.3 Remove Flag Argument`, `6.9 Combine Functions into Class` | Keep explicit params when decoupling pure logic from globals (`11.6`) |
| 5 | **Global Data** | `6.6 Encapsulate Variable`, `11.7 Remove Setting Method`, `8.1`/`8.2` Move into narrow module | Small read-only startup constants are far less toxic than mutable globals |
| 6 | **Mutable Data** | `6.6 Encapsulate Variable`, `9.1 Split Variable`, `11.1 Separate Query from Modifier`, `9.3 Replace Derived Variable with Query`, `9.4 Change Reference to Value` | Localized mutation wrapped behind narrow class/module boundaries is safe |
| 7 | **Divergent Change** | `6.11 Split Phase`, `8.1 Move Function`, `7.5 Extract Class` | Group code so each module has **one clear axis of change** |
| 8 | **Shotgun Surgery** | `8.1 Move Function`, `8.2 Move Field`, `6.9`/`6.10` Combine Functions, tactical `6.2`/`7.6` Inline then re-extract | Inverse of Divergent Change: pull scattered edits together |
| 9 | **Feature Envy** | `8.1 Move Function` (after `6.1 Extract Function` on envious slice if partial) | Strategy, Visitor, and Self-Delegation isolate volatile behavior intentionally |
| 10 | **Data Clumps** | `7.5 Extract Class`, `6.8 Introduce Parameter Object`, `11.4 Preserve Whole Object` | Delete-one-field test: if remaining fields lose meaning, make an object |
| 11 | **Primitive Obsession** | `7.3 Replace Primitive with Object`, `12.6`/`12.10` + `10.4` Polymorphism, `6.8 Introduce Parameter Object` | Watch out for **"stringly typed"** variables encoding domain rules |
| 12 | **Repeated Switches** | `10.4 Replace Conditional with Polymorphism` (`12.6` Subclasses or `12.10` Delegate) | A **single** isolated switch (e.g., factory) is completely fine! |
| 13 | **Loops** | `8.8 Replace Loop with Pipeline`, `8.7 Split Loop` | Split multi-accumulator loops (`8.7`) before converting to pipelines |
| 14 | **Lazy Element** | `6.2 Inline Function`, `7.6 Inline Class`, `12.9 Collapse Hierarchy` | Keep 1-line helpers when the name clarifies domain intent |
| 15 | **Speculative Generality** | `12.9 Collapse Hierarchy`, `6.2 Inline Function`, `6.5 Change Function Declaration`, `8.9 Remove Dead Code` | Clue: parameters/hooks whose **only** callers are test cases |
| 16 | **Temporary Field** | `7.5 Extract Class`, `8.1 Move Function`, `11.9 Replace Function with Command`, `10.5 Introduce Special Case` | Fields populated only inside one algorithm belong on a dedicated object |
| 17 | **Message Chains** | `7.7 Hide Delegate`, or `6.1 Extract Function` + `8.1 Move Function` down the chain | Prefer moving client behavior down the chain over creating a Middle Man |
| 18 | **Middle Man** | `7.8 Remove Middle Man`, `6.2 Inline Function`, `12.11 Replace Superclass with Delegate` | Keeping a small handful of high-value convenience forwarders is fine |
| 19 | **Insider Trading** | `8.1 Move Function`, `8.2 Move Field`, `7.5 Extract Class`, `7.7 Hide Delegate`, `12.10`/`12.11` Delegate | Subclasses knowing too much about superclass internals need delegation |
| 20 | **Large Class** | Intra-class `6.1 Extract Function` first, then `7.5 Extract Class`, `12.8 Extract Superclass`, `12.6`/`12.10` | Deduplicate methods *inside* the class first, and inspect client usage subsets |
| 21 | **Alternative Classes with Different Interfaces** | `6.5 Change Function Declaration`, `8.1 Move Function`, `12.8 Extract Superclass` | Align signatures and protocols until classes become substitutable |
| 22 | **Data Class** | `7.1 Encapsulate Record`, `11.7 Remove Setting Method`, `8.1 Move Function` from clients | **Immutable intermediate records** (`6.10`, `6.11`) are healthy, not a smell! |
| 23 | **Refused Bequest** | `12.4 Push Down Method`, `12.5 Push Down Field`, or `12.11`/`12.10` Replace with Delegate | Mild if subtype contract holds; **severe** if public contract is refused |
| 24 | **Comments (Deodorant)** | `6.1 Extract Function`, `6.5 Change Function Declaration`, `10.6 Introduce Assertion` | Keep comments explaining **why**, tradeoffs, API quirks, or uncertainty |

## Detailed Diagnostic Notes & Ordered Remedies

### 1. Mysterious Name

- **Symptom**: Functions, modules, variables, or record fields carry vague, abbreviated, or misleading names (`proc()`, `data2`, `flag`, `tpHd`, `handle()`), forcing readers to reverse-engineer implementation lines.
- **Diagnostic Insight**: Persistent difficulty finding a crisp name is a strong signal that the element mixes multiple responsibilities - split it first (`6.1 Extract Function` / `6.11 Split Phase`), and clear names will emerge naturally.
- **Ordered Remedies**:
  1. Functions/methods: `6.5 Change Function Declaration` (`references/ch06-first-set.md`)
  2. Variables/constants: `6.7 Rename Variable` (encapsulate first via `6.6 Encapsulate Variable` if module/global)
  3. Record/class properties: `9.2 Rename Field` (`references/ch09-organizing-data.md`)

### 2. Duplicated Code

- **Symptom**: Identical or structurally isomorphic expressions, statement sequences, validation blocks, or algorithms appearing in two or more places.
- **Ordered Remedies**:
  1. Same function/module: `8.6 Slide Statements` to bring similar lines together -> `6.1 Extract Function` -> `8.5 Replace Inline Code with Function Call`.
  2. Identical structure differing only by literal constants/thresholds: `11.2 Parameterize Function` (`references/ch11-refactoring-apis.md`).
  3. Repeated setup/teardown around every call to a function: `8.3 Move Statements into Function`.
  4. Sibling subclasses: `6.1 Extract Function` on differing hooks -> `12.1 Pull Up Method` (+ `12.2 Pull Up Field` / `12.3 Pull Up Constructor Body`).
  5. Separate unrelated classes: `12.8 Extract Superclass` or `7.5 Extract Class` shared by composition.

### 3. Long Function (1e: *Long Method*)

- **Symptom**: Functions spanning dozens of lines where business *intent* is buried under low-level loops, temporaries, and nested branches.
- **Heuristic**: Small functions live on good names. Whenever you feel tempted to write a comment above 3 lines of code explaining what they do, extract those lines into a function named after that comment - even for a single line if intent and implementation diverge (`highlight()` calling `reverse()`).
- **Ordered Remedies**:
  1. Primary workhorse (99% of cases): `6.1 Extract Function` (`references/ch06-first-set.md`).
  2. Many local temps creating long extracted parameter lists: `7.4 Replace Temp with Query` + `9.1 Split Variable`.
  3. Clumped parameters passed across helpers: `6.8 Introduce Parameter Object` + `11.4 Preserve Whole Object`.
  4. Deeply knotted parameters and mutable locals resisting extraction: `11.9 Replace Function with Command`.
  5. Conditionals dominating the body: `10.1 Decompose Conditional`, `10.3 Replace Nested Conditional with Guard Clauses`, or `10.4 Replace Conditional with Polymorphism`.
  6. Loops computing multiple values: `8.7 Split Loop` -> `6.1 Extract Function`.
  7. Sequential parse -> compute -> format stages: `6.11 Split Phase`.

### 4. Long Parameter List

- **Symptom**: Signatures taking 4+ parameters, forcing callers to unpack objects or memorize positional boolean/primitive orderings.
- **Legitimate Exception**: When intentionally breaking a dependency on a global or heavyweight entity so a calculation stays pure (`11.6 Replace Query with Parameter`), an explicit parameter is healthier than hidden coupling.
- **Ordered Remedies**:
  1. Parameter easily derived from another parameter or `this`: `11.5 Replace Parameter with Query`.
  2. Multiple values unpacked from one existing object: `11.4 Preserve Whole Object`.
  3. Related values traveling together without a host object: `6.8 Introduce Parameter Object`.
  4. Boolean/enum mode selector telling the function which branch to run: `11.3 Remove Flag Argument`.
  5. Multiple functions sharing the exact same parameter bundle: `6.9 Combine Functions into Class` *(in functional programming styles, this corresponds to creating a set of partially applied functions closing over the shared configuration/record)*.

### 5. Global Data

- **Symptom**: Mutable global variables, module-level singletons, class/static variables, or exported config maps writable from anywhere in the codebase without an access seam.
- **Paracelsus Dose Nuance**: *"The difference between poison and medicine is the dose."* Small doses of genuinely immutable, startup-initialized global constants are tolerable; **mutable** global data is intensely toxic because no mechanism tells you which module silently altered it.
- **Ordered Remedies**:
  1. Non-negotiable first move: `6.6 Encapsulate Variable` (`references/ch06-first-set.md`) so every read/write passes through functions.
  2. Lock down mutations with `11.7 Remove Setting Method` or return defensive clones, then move encapsulated state into a narrow class/module (`8.1 Move Function` + `8.2 Move Field`).

### 6. Mutable Data

- **Symptom**: In-place modification of variables, records, or arrays causing action-at-a-distance bugs when distant code assumes prior values, or cached derived totals drifting out of sync.
- **Ordered Remedies**:
  1. Gate all mutations through narrow functions: `6.6 Encapsulate Variable`, `7.1 Encapsulate Record`, `7.2 Encapsulate Collection`.
  2. Single local variable reassigned for two different roles: `9.1 Split Variable` (`references/ch09-organizing-data.md`).
  3. Separate pure computation from state-mutating code: `8.6 Slide Statements` + `6.1 Extract Function` + `11.1 Separate Query from Modifier`.
  4. Forbid post-construction mutation: `11.7 Remove Setting Method`.
  5. Mutable field merely storing a computable sum/status: `9.3 Replace Derived Variable with Query` (especially pungent!).
  6. Restrict mutation radius or switch to full immutability: `6.9 Combine Functions into Class`, `6.10 Combine Functions into Transform` (read-only pipelines), or `9.4 Change Reference to Value` (immutable Value Objects).

### 7. Divergent Change

- **Symptom**: A single module or class changes frequently in different ways for orthogonal reasons ("Every time we add a database we edit these 3 methods; every time we add a financial product we edit these 4 methods").
- **Diagnostic Goal**: Align module boundaries so each module has **one clear axis of change**; ignore everything unrelated to that axis when working inside it.
- **Ordered Remedies**:
  1. Sequential pipeline concerns (e.g., parsing/DB fetch -> business logic -> formatting): `6.11 Split Phase` with a clean intermediate data structure.
  2. Interleaved back-and-forth calls: `6.1 Extract Function` for each concern -> `8.1 Move Function` / `7.5 Extract Class` to split into dedicated modules per context.

### 8. Shotgun Surgery

- **Symptom**: Mirror opposite of Divergent Change - making one conceptual change requires hunting down and making tiny edits across 6-10 different files/classes.
- **Ordered Remedies**:
  1. Co-locate scattered logic and state: `8.1 Move Function` and `8.2 Move Field` into a single owning module.
  2. Functions operating on the same raw data across files: `6.9 Combine Functions into Class` or `6.10 Combine Functions into Transform`.
  3. Shared upstream data preparation feeding multiple consumers: `6.11 Split Phase`.
  4. Tactical Consolidation Pattern: apply `6.2 Inline Function` or `7.6 Inline Class` first to pull badly scattered fragments into one visible body, then re-extract cleanly (`6.1 Extract Function` / `7.5 Extract Class`).

### 9. Feature Envy

- **Symptom**: A function in Module A spends far more lines reading getters and computing over Module B's fields than interacting with Module A's own state.
- **Legitimate Exception**: Strategy, Visitor, and Kent Beck's Self-Delegation deliberately isolate volatile behavior *away* from stable domain data to cure *Divergent Change*. Do not merge a Strategy back into the data class if independent variation is the whole point.
- **Ordered Remedies**:
  1. Entire function envies another class/record: `8.1 Move Function` into that class.
  2. Sub-slice of a function envies another object: `6.1 Extract Function` on that slice -> `8.1 Move Function`.
  3. Touches several objects: decompose into small extracted functions first, then move each helper to the module holding the majority of its referenced data.

### 10. Data Clumps

- **Symptom**: Identical 2-5 data fields (`min`/`max`, `amount`/`currency`, `latitude`/`longitude`, `street`/`city`/`postalCode`) traveling together across multiple class definitions and function parameter lists.
- **Litmus Test**: Delete one value from the group - if the remaining values lose coherent domain meaning, they belong inside their own object.
- **Ordered Remedies**:
  1. Clumped class fields: `7.5 Extract Class` (`references/ch07-encapsulation.md`).
  2. Clumped function parameters: `6.8 Introduce Parameter Object` or `11.4 Preserve Whole Object`.
  3. Always follow through: migrate range/validation/formatting logic onto the new class via `8.1 Move Function` so it becomes a rich Value Object (`9.4 Change Reference to Value`) rather than an empty struct.

### 11. Primitive Obsession

- **Symptom**: Using raw strings, ints, or floats to represent structured domain concepts (`Priority`, `Money`, `PhoneNumber`, `TaxRate`, `OrderStatus`), breeding **"stringly typed"** variables where regex checks, string comparisons (`"high" === o.priority || "rush" === o.priority`), and unit-conversion bugs scatter everywhere.
- **Ordered Remedies**:
  1. Give the concept a proper Value Object: `7.3 Replace Primitive with Object` + `9.4 Change Reference to Value`.
  2. Primitive acts as a type code controlling conditional behavior: `12.6 Replace Type Code with Subclasses` (or `12.10 Replace Subclass with Delegate`) + `10.4 Replace Conditional with Polymorphism`.
  3. Recurring clusters of primitives: `7.5 Extract Class` + `6.8 Introduce Parameter Object`.

### 12. Repeated Switches (1e: *Switch Statements*)

- **Symptom**: The *same* `switch`/`case` or `if/else if` ladder branching on the *same* type/status discriminator appears in two or more places, meaning every newly added variant forces synchronized edits across all switches.
- **Legitimate Exception**: Fowler renamed this from *Switch Statements* to *Repeated Switches* in the 2nd Edition because a **single** `switch` (e.g., inside a factory function or isolated single dispatch point) is completely benign! Refactor to polymorphism only when the conditional logic is *duplicated* across behaviors or excessively complex.
- **Ordered Remedies**:
  1. `10.4 Replace Conditional with Polymorphism` (`references/ch10-simplifying-conditionals.md`), backed by `12.6 Replace Type Code with Subclasses` or `12.10 Replace Subclass with Delegate`.

### 13. Loops

- **Symptom**: Classic imperative `for`/`while` loops with index variables, `continue`/`break` flags, and mutable accumulators obscuring what elements are selected and how they are transformed.
- **Ordered Remedies**:
  1. Loop performing two accumulations at once: `8.7 Split Loop` (`references/ch08-moving-features.md`).
  2. Control flag cluttering loop exit: `10.3 Replace Nested Conditional with Guard Clauses` / `6.1 Extract Function` with early `return`.
  3. Express data transformation declaratively (`filter`, `map`, `flatMap`, `reduce`, `find`, `some`): `8.8 Replace Loop with Pipeline`.

### 14. Lazy Element (1e: *Lazy Class*)

- **Symptom**: Program elements (one-line wrapper functions whose name equals their implementation, classes reduced to a single trivial method after refactoring, or one-child inheritance hierarchies) that add ceremony without earning their keep.
- **Legitimate Exception**: Keep a one-line function whenever its name bridges a genuine gap between *intent* and *implementation*!
- **Ordered Remedies**:
  1. `6.2 Inline Function`
  2. `7.6 Inline Class`
  3. `12.9 Collapse Hierarchy`

### 15. Speculative Generality

- **Symptom**: Unused abstract base classes, "just-in-case" hook methods, optional parameters always passed the same constant, or indirection layers whose **only callers are unit tests**.
- **Ordered Remedies**:
  1. Pointless abstract parent/child split: `12.9 Collapse Hierarchy`.
  2. Unused delegation layers: `6.2 Inline Function` + `7.6 Inline Class`.
  3. Unused parameters or constant-only parameters: `6.5 Change Function Declaration`.
  4. Unreferenced functions/branches (delete outdated test-only callers first): `8.9 Remove Dead Code`.

### 16. Temporary Field

- **Symptom**: Instance variables on a class that are populated only during one complex method execution (passed via fields to avoid long parameter lists) and sit `null`/meaningless for the rest of the object's lifecycle.
- **Ordered Remedies**:
  1. Move the orphan fields and every helper referencing them into a dedicated component or Method Object: `7.5 Extract Class` + `8.1 Move Function`, or `11.9 Replace Function with Command`.
  2. Eliminate `if (field !== null)` checks around invalid/unpopulated states: `10.5 Introduce Special Case`.

### 17. Message Chains

- **Symptom**: Client code navigating deep object graphs (`order.customer.department.manager.office.phone`), tightly coupling the caller to every intermediate class relationship.
- **Ordered Remedies**:
  1. Hide navigation behind delegating accessors: `7.7 Hide Delegate` (`references/ch07-encapsulation.md`).
  2. Prefer behavioral Push over Middle-Man bloat: inspect what the client ultimately computes with that final object -> `6.1 Extract Function` -> `8.1 Move Function` down the chain!

### 18. Middle Man

- **Symptom**: Overzealous encapsulation where half of a class's interface consists of one-line methods forwarding straight to an internal delegate.
- **Ordered Remedies**:
  1. Let clients talk to the delegate directly: `7.8 Remove Middle Man` + `6.2 Inline Function`.
  2. If the wrapper genuinely *is* a subtype of the delegate conceptually (supports 100% of its contract), consider real inheritance; if inheritance was misused, keep only meaningful domain methods (`12.11 Replace Superclass with Delegate`).

### 19. Insider Trading (1e: *Inappropriate Intimacy*)

- **Symptom**: Modules trading excessive private data behind the scenes, bidirectional back-pointers chatting constantly, or subclasses coupled tightly to mutable private details of their superclass.
- **Ordered Remedies**:
  1. Separate or merge chatty pieces: `8.1 Move Function` and `8.2 Move Field` to put cohesive pieces in one place.
  2. Extract their shared secret into a third mediating value/domain class (`7.5 Extract Class`) or break bidirectional coupling (`7.7 Hide Delegate`).
  3. Subclass/superclass over-coupling: `12.10 Replace Subclass with Delegate` or `12.11 Replace Superclass with Delegate`.

### 20. Large Class

- **Symptom**: Classes hoarding 15+ fields or dozens of methods, inevitably breeding duplicated code and divergent change.
- **Two High-Leverage Diagnostic Moves (Ch. 3.20)**:
  1. **Deduplicate inside the class first**: Before splitting a giant class, eliminate duplication among its own methods via `6.1 Extract Function` (e.g., turning five 100-line methods sharing similar logic into five 10-line methods calling ten 2-line private helpers makes the real component boundaries jump off the screen!).
  2. **Inspect client usage subsets**: Ask clients how they use the class - if group A of callers always touches fields/methods `{X, Y}` while group B touches `{Z, W}`, each client-facing subset marks a clean seam for `7.5 Extract Class` or `12.8 Extract Superclass`!
- **Ordered Remedies**:
  1. Intra-class `6.1 Extract Function` to surface shared helpers and field clusters.
  2. Component composition (default): `7.5 Extract Class` (look for common field prefixes/suffixes like `officeAreaCode`/`officeNumber`).
  3. Shared hierarchical abstraction: `12.8 Extract Superclass`.
  4. Internal mode/type flags splitting class behavior: `12.6 Replace Type Code with Subclasses` or `12.10 Replace Subclass with Delegate`.

### 21. Alternative Classes with Different Interfaces

- **Symptom**: Two classes model interchangeable concepts (e.g., `StripeGateway` vs. `AdyenGateway`) but have incompatible method names and parameter layouts, blocking polymorphic substitution.
- **Ordered Remedies**:
  1. Unify method names and parameter lists: `6.5 Change Function Declaration`.
  2. Migrate missing protocol responsibilities into the classes until contracts match: `8.1 Move Function`.
  3. Extract shared base code if duplication emerges: `12.8 Extract Superclass`.

### 22. Data Class

- **Symptom**: Passive containers holding only fields and getters/setters while external service/utility classes reach in, read 4 fields, and compute results that belong on the class itself.
- **Legitimate Exception**: **Immutable intermediate result records** created by `6.11 Split Phase` or `6.10 Combine Functions into Transform` (e.g., Data Transfer / View Model records passed straight to a template renderer) are **not** a smell! Because their fields are immutable, they require neither getters nor encapsulation.
- **Ordered Remedies**:
  1. Public mutable record: `7.1 Encapsulate Record`.
  2. Freeze identity/invariant fields: `11.7 Remove Setting Method`.
  3. Locate client code operating on those getters -> `6.1 Extract Function` -> `8.1 Move Function` into the Data Class.

### 23. Refused Bequest

- **Symptom**: A subclass inherits fields, methods, or public contracts from its superclass that do not apply to it.
- **Critical Distinction**:
  - *Case A - Subclass supports the superclass **interface** (is substitutable), just ignores some inherited implementation*: Mild smell. Either leave it if harmless, or push sibling-only fields/methods down (`12.4 Push Down Method`, `12.5 Push Down Field`).
  - *Case B - Subclass reuses implementation code while **refusing the superclass public contract** (e.g., throwing `UnsupportedOperationException` or breaking Liskov substitution)*: **Strong smell!** Never leave broken inheritance; switch to delegation immediately.
- **Ordered Remedies**:
  1. Implementation sitting too high in a valid hierarchy: `12.4 Push Down Method` + `12.5 Push Down Field`.
  2. Invalid subtype contract: `12.11 Replace Superclass with Delegate` or `12.10 Replace Subclass with Delegate`.

### 24. Comments (Used as Deodorant)

- **Symptom**: Thick narrative comments explaining *what* convoluted blocks do because variable names, expressions, and 100-line functions fail to speak for themselves.
- **Legitimate Good Comments (Always Keep!)**:
  - Explaining **why** a non-obvious design or performance tradeoff was chosen over an intuitive alternative.
  - Recording external API quirks, hardware errata, regex examples, or areas of unfinished uncertainty (`TODO` with context).
- **Ordered Remedies**:
  1. Comment narrates what a code block does: `6.1 Extract Function` using the comment's phrasing as the function name, then delete the comment.
  2. Comment explains what an existing function/parameter means: `6.5 Change Function Declaration` + `6.7 Rename Variable`.
  3. Comment warns `"assumes x is already normalized and > 0"`: encode as executable check via `10.6 Introduce Assertion`.
