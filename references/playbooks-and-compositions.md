# Composite Refactoring Playbooks (Ch. 1, Ch. 10 & Ch. 12 Multi-Move Sequences)

Individual refactorings look tiny in isolation; their real power comes from **chaining them in disciplined sequences** where each micro-step unlocks the next while tests stay green throughout. Use these seven canonical Fowler playbooks when tackling real-world modules.

## Playbook 1: Monolithic Procedure -> Split Phase -> Polymorphic Calculator (Fowler Ch. 1)

**Scenario**: A long function (`statement(invoice, plays)`) interleaves data lookups, conditional domain calculations (pricing/credits by type), loop accumulations, currency formatting, and plain-text output rendering - and now you need an HTML version (`htmlStatement`) plus new play categories without copy-pasting.

### Sequence of Moves (Including Ch. 1 Micro-Conventions)

1. **Extract Type-Switched Calculation (`6.1 Extract Function` + `6.7 Rename Variable`)**:
   - Extract the inner `switch` block into `amountFor(aPerformance, play)`.
   - Rename the return accumulator to `result` (Fowler's standard convention so its role is unmistakable) and type-hint parameters with indefinite articles (`aPerformance`) in untyped languages. *Compile-Test-Commit after every green step!*
2. **Eliminate Passed Lookup Temps (`7.4 Replace Temp with Query` + `6.4 Inline Variable` + `6.5 Change Function Declaration`)**:
   - Extract `playFor(aPerformance)` as a query, inline `const play = playFor(perf)` at call sites, and remove the `play` parameter from `amountFor(aPerformance)` so helpers stop threading derived locals. `[Test]`
3. **Convert Function Variables & Centralize Unit Scaling (`6.5 Change Function Declaration`)**:
   - Convert `const format = new Intl.NumberFormat(...).format;` into an explicit domain function `function usd(aNumber)` and move repeated `/ 100` cent-to-dollar division inside `usd(aNumber)` so all internal money calculations remain in integer cents. `[Test]`
4. **Untangle Loop Accumulators & Resolve Name Collisions (`8.7 Split Loop` + `8.6 Slide Statements` + `6.1 Extract Function` + `6.4 Inline Variable`)**:
   - Extract `volumeCreditsFor(aPerformance)`. Split the main loop so volume-credit accumulation runs in its own loop, slide `let volumeCredits = 0` right above that loop, extract `totalVolumeCredits()`, and inline the temp.
   - **Temp-Name Collision Workaround**: When extracting `totalAmount` while a local variable `let totalAmount` already exists in scope, extract under an arbitrary placeholder name first (`function appleSauce()`), apply `6.4 Inline Variable` on `totalAmount`, then rename `appleSauce` -> `totalAmount` (`6.5 Change Function Declaration`)! `[Test after each sub-step]`
5. **Separate Calculation from Formatting (`6.11 Split Phase` + `8.8 Replace Loop with Pipeline`)**:
   - Extract the text-rendering body into `renderPlainText(data)`.
   - Create `createStatementData(invoice, plays)` returning an immutable intermediate record `statementData` (cloning records inside `enrichPerformance` via `Object.assign({}, aPerformance)` so input data stays untouched!), moving `customer`, `performances`, `play`, `amount`, `volumeCredits`, `totalAmount`, and `totalVolumeCredits` onto `statementData` one field at a time, and replacing accumulator loops with `.reduce(...)` pipelines. `[Test]`
   - Extract `createStatementData` into its own module (`statement.js` + `createStatementData.js`), then write `htmlStatement` in 12 lines sharing `createStatementData`!
6. **Replace Type Switches with Polymorphic Calculator (`11.8 Replace Constructor with Factory Function` + `12.6 Replace Type Code with Subclasses` + `8.1 Move Function` + `10.4 Replace Conditional with Polymorphism`)**:
   - Create `createPerformanceCalculator(aPerformance, aPlay)` switching on `aPlay.type` to return `new TragedyCalculator(...)` or `new ComedyCalculator(...)` extending `PerformanceCalculator`.
   - **Base Default vs. Abstract Error Rule**:
     - Every play category computes `amount` differently -> `PerformanceCalculator.amount` throws `new Error("subclass responsibility")` while `TragedyCalculator` and `ComedyCalculator` override `get amount()`.
     - Most play categories share `Math.max(audience - 30, 0)` for `volumeCredits` and only comedy adds extra credits -> keep the common baseline in `PerformanceCalculator.volumeCredits` and have `ComedyCalculator.volumeCredits` return `super.volumeCredits + Math.floor(this.performance.audience / 5)`!
   - Copy `calculator.amount` and `calculator.volumeCredits` onto the enriched `statementData` record rather than returning raw calculator instances so the intermediate data structure hides polymorphic implementation details. `[Test]`

```javascript
// Final architecture after Playbook 1:
export function statement(invoice, plays) {
  return renderPlainText(createStatementData(invoice, plays));
}

export function createStatementData(invoice, plays) {
  const enrichPerformance = (aPerformance) => {
    const calculator = createPerformanceCalculator(aPerformance, playFor(aPerformance));
    const result = Object.assign({}, aPerformance);
    result.play = calculator.play;
    result.amount = calculator.amount;
    result.volumeCredits = calculator.volumeCredits;
    return result;
  };
  const performances = invoice.performances.map(enrichPerformance);
  return {
    customer: invoice.customer,
    performances,
    totalAmount: performances.reduce((sum, p) => sum + p.amount, 0),
    totalVolumeCredits: performances.reduce((sum, p) => sum + p.volumeCredits, 0),
  };
}
```

## Playbook 2: Imperative Multi-Accumulator Loop -> Clean Pipelines

**Scenario**: A single `for` loop filters records, mutates two different counters/maps, and tracks a min/max value.

### Sequence of Moves

1. **Check Side Effects**: Confirm loop body expressions do not mutate elements of the source collection itself (if they do, apply `11.1 Separate Query from Modifier` first).
2. **`8.7 Split Loop`**: Duplicate the loop once per independent output variable and delete the other variable's lines from each copy. `[Test]`
3. **`8.6 Slide Statements`**: Slide each accumulator declaration immediately above its dedicated loop. `[Test]`
4. **`6.1 Extract Function`**: Extract each single-purpose loop into a named pure query function. `[Test]`
5. **`8.8 Replace Loop with Pipeline`**: Inside each small query function, convert `if` guards to `.filter(...)` and accumulations to `.map(...)` / `.reduce(...)` / `Math.min(...)`. `[Test]`

## Playbook 3: Deeply Knotted Algorithm -> Command (Method Object) Decomposition

**Scenario**: A 150-line `score(candidate, medicalExam, scoringGuide)` function mutates 6 local flags and accumulators (`result`, `healthLevel`, `highMedicalRiskFlag`, `certificationGrade`), causing `6.1 Extract Function` to stall because every slice needs 5 in/out parameters.

### Sequence of Moves

1. **`11.9 Replace Function with Command`**: Create `class Scorer` with `execute(...)` containing the exact body of `score(...)`, and turn `score(...)` into `return new Scorer().execute(...)`. `[Test]`
2. **Promote Parameters to Fields**: Move parameters from `execute(...)` to `constructor(candidate, medicalExam, scoringGuide)` one parameter at a time, storing `this._candidate`, etc. `[Test after each]`
3. **`9.1 Split Variable` + Promote Locals to Fields**: Split any local variable reused for two meanings, then turn shared local variables (`let healthLevel = 0`) into instance fields (`this._healthLevel = 0`). `[Test]`
4. **Zero-Argument `6.1 Extract Function`**: Extract cohesive chunks (`this.scoreSmoking()`, `this.scoreCertification()`) as clean zero-parameter methods sharing instance fields, and apply `10.1 Decompose Conditional` on dense conditions. `[Test]`

## Playbook 4: Rigid Inheritance -> Dynamic / Full-Hierarchy Delegation & Reference Splitting (Ch. 12.10 & 12.11)

### Variant 4A: Single Subclass or Full Subclass Hierarchy -> Delegate (`12.10`)

**Scenario**: Either `PremiumBooking extends Booking` needs dynamic runtime promotion (`bePremium()`), OR `Bird` has 4 species subclasses (`EuropeanSwallow`, `AfricanSwallow`, ...) and now needs an orthogonal inheritance hierarchy (`WildBird` vs. `CaptiveBird`).

1. **`11.8 Replace Constructor with Factory Function`**: Wrap `new Booking(...)` / `new Bird(...)` behind factory functions. `[Test]`
2. **Introduce Delegate(s) & Host Reference**:
   - *Single optional subclass (`PremiumBooking`)*: Attach `_premiumDelegate = new PremiumBookingDelegate(this, extras)`. When moving overrides that called `super.basePrice`, avoid infinite recursion either via `_privateBasePrice` on `Booking` or `this._premiumDelegate.extendBasePrice(result)`!
   - *Full species hierarchy (`Bird`)*: Create species delegates (`EuropeanSwallowDelegate`, `AfricanSwallowDelegate`, `NorwegianBlueParrotDelegate`), then apply `12.8 Extract Superclass` across the delegates to create `SpeciesDelegate(data, bird)` and initialize `this._speciesDelegate = this.selectSpeciesDelegate(data)` (defaulting to `new SpeciesDelegate(data, this)`). Now `Bird` has **zero `if` checks** (`get plumage() { return this._speciesDelegate.plumage; }`) while `Bird` is free to subclass into `WildBird`/`CaptiveBird` and `SpeciesDelegate` cleanly shares bird-species code via inheritance! `[Test]`

### Variant 4B: Broken "Type-Instance Homonym" Superclass -> Shared Reference Delegate (`12.11` + `9.5`)

**Scenario**: Physical copy `Scroll extends CatalogItem` passes both physical copy cleaning dates and catalog title/tags to `super(id, title, tags)`, duplicating catalog metadata and conflating copy ID with catalog item ID.

1. **`12.11 Replace Superclass with Delegate`**: Add `this._catalogItem = new CatalogItem(null, title, tags)` on `Scroll` (passing `null` temporarily to stop conflating `Scroll.id` with `CatalogItem.id`!), forward `title` and `hasTag(s)` to `this._catalogItem`, and delete `extends CatalogItem`. `[Test]`
2. **`9.5 Change Value to Reference`**: Pass `catalogID` and `catalog` repository into `new Scroll(id, dateLastCleaned, catalogID, catalog)` (`6.5 Change Function Declaration`) and set `this._catalogItem = catalog.get(catalogID)` so all physical copies of the same scroll share one canonical `CatalogItem`! `[Test]`

## Playbook 5: Raw Mutable Hash/Global -> Encapsulated Domain & Value Objects

**Scenario**: Raw JSON objects, primitive strings (`"rush"`), and shared arrays circulate across 20 modules with direct property writes (`org.usages[year][month] = v; person.courses.push(c);`).

### Sequence of Moves

1. **`6.6 Encapsulate Variable`**: Wrap global/module data access behind `getRawDataOfX()` and `setRawDataOfX()`. `[Test]`
2. **`7.1 Encapsulate Record` (Mutations First!)**: Wrap the raw data in `class XData`, extract every deep write into explicit mutators (`setUsage(id, year, month, amount)`), and verify zero missed direct writes by returning `structuredClone` or frozen views on reads. `[Test]`
3. **`7.2 Encapsulate Collection`**: Replace external `.push()` / `.splice()` calls with `addCourse()` / `removeCourse()`, and make collection getters return shallow copies (`slice()`). `[Test]`
4. **`7.3 Replace Primitive with Object` + `9.4 Change Reference to Value`**: Promote domain primitives (`Priority`, `Money`, `DateRange`) into immutable Value Objects with `equals()` and `11.7 Remove Setting Method`, then pull client comparison/formatting logic inward via `8.1 Move Function`. `[Test]`

## Playbook 6: Wide Fan-Out Signature or Schema Change Without Breaking Trunk

**Scenario**: Changing a function called in 90 files (e.g., decoupling `inNewEngland(customer)` -> `inNewEngland(stateCode)`) or renaming a serialized field/database column.

### Sequence of Moves (Function Migration Mechanics, `6.5`)

1. **Prepare Body (`6.3 Extract Variable`)**: Inside `inNewEngland(aCustomer)`, extract `const stateCode = aCustomer.address.state;` right at the top. `[Test]`
2. **Extract New Target Signature (`6.1 Extract Function`)**: Extract the rest of the body into `xxNEWinNewEngland(stateCode)`. `[Test]`
3. **Inline Temp in Wrapper (`6.4 Inline Variable`)**: Simplify the old function to `return xxNEWinNewEngland(aCustomer.address.state);`. `[Test]`
4. **Incremental Caller Migration (`6.2 Inline Function`)**: Inline `inNewEngland` into callers 5-10 files at a time so callers become `xxNEWinNewEngland(c.address.state)`, running tests after every batch. `[Test]`
5. **Finalize Name (`6.5 Change Function Declaration`)**: Once the old wrapper is deleted, rename `xxNEWinNewEngland` -> `inNewEngland`. `[Test]`
   *(For databases or cross-service JSON contracts, follow `assets/templates/parallel-change-checklist.md` instead.)*

## Playbook 7: Base-and-Variant ("Programming by Difference") Polymorphism (Ch. 10.4 `Rating` Case)

**Scenario**: Unlike textbook `switch (type)` hierarchies with no default case, business rules often have a **standard calculation** (`Rating`) plus a **special-case variant** (`hasChina && voyage.zone === "china"`) woven through 4 different `if/else` sub-clauses inside `captainHistoryRisk` and `voyageProfitFactor`.

### Sequence of Moves

1. **Isolate Sub-Calculations First (`6.1 Extract Function`)**: Extract mixed conditional clauses into named helper functions before introducing classes. `[Test]`
2. **Create Base Class & Variant Subclass (`6.9 Combine Functions into Class` + `11.8 Factory`)**:
   - Move the rating functions into `class Rating` and create `class ExperiencedChinaRating extends Rating`.
   - Create `createRating(voyage, history)` returning `new ExperiencedChinaRating(voyage, history)` when `voyage.zone === "china" && hasChina(history)`, else `new Rating(voyage, history)`. `[Test]`
3. **Override Clean Methods Directly (`10.4 Replace Conditional with Polymorphism`)**:
   - Override `get captainHistoryRisk()` in `ExperiencedChinaRating` as `Math.max(super.captainHistoryRisk - 2, 0)` and delete the China branch from `Rating.captainHistoryRisk`. `[Test]`
4. **Separate Interleaved Variant Branches via Temporary `"And"` Method + `8.4 Move Statements to Callers`**:
   - When `voyageProfitFactor` tangles China-specific history bonuses and voyage-length bonuses inside one `if`, extract the entire `if/else` block into `get voyageAndHistoryLengthFactor()` (the `"And"` in the name deliberately signals two mixed concerns!).
   - Move the China leg onto `ExperiencedChinaRating.voyageAndHistoryLengthFactor` and leave the standard leg on `Rating`. `[Test]`
   - Now extract `get historyLengthFactor()` separately in *both* `Rating` (`history.length > 8 ? 1 : 0`) and `ExperiencedChinaRating` (`history.length > 10 ? 1 : 0`), use `8.4 Move Statements to Callers` on `Rating.voyageAndHistoryLengthFactor` so `historyLengthFactor` moves up into `Rating.voyageProfitFactor` (where `ExperiencedChinaRating` inherits it polymorphically!), and rename the remaining single-concern method `voyageAndHistoryLengthFactor` -> `voyageLengthFactor` (`6.5`)! `[Test]`
