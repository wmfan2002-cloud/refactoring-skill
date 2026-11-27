# Principles, Catalog Mechanics & Self-Testing Code (Preface, Ch. 2, Ch. 4 & Ch. 5)

Operational distillation of Martin Fowler's Preface, Chapter 2 (*Principles in Refactoring*), Chapter 4 (*Building Tests*), and Chapter 5 (*Introducing the Catalog*). Load this guide when deciding *whether* and *when* to refactor, calibrating step granularity across static vs. dynamic languages, handling published interfaces or databases, tuning performance, or building tests around legacy code.

## 1. Precise Definition & The Consultant Parable

- **Refactoring (noun)**: A change made to the internal structure of software to make it easier to understand and cheaper to modify without changing its observable behavior.
- **Refactoring (verb)**: Restructuring software by applying a series of refactorings without changing its observable behavior.
- **Critical Litmus Test**: *Restructuring* is any code cleanup or reorganization. *Refactoring* is a specific discipline built on tiny, behavior-preserving steps where the codebase never stays broken. **If someone says their code has been broken for two days "while refactoring," they are not refactoring - they are doing uncontrolled restructuring.**
- **Observable Behavior Nuance**: Call stacks, internal module interfaces, and non-critical timing change during refactoring (`Extract Function`, `Move Function`), which is expected. However, user-observable inputs, outputs, side effects, and even *currently relied-upon or externally visible bugs* remain untouched under the Refactoring Hat (fix bugs separately under the Bugfix Hat).
- **The Preface Consultant Parable ("If It Works, Don't Touch It" Collapse)**: Fowler opens the book with a large project where early developers created a tangled class hierarchy. Management forbade cleaning it up because it appeared to work and carried no immediate feature ticket. Six months later the entire project collapsed because the code had grown too complex to debug or tune for acceptable performance - only succeeding after restarting from scratch with Kent Beck enforcing continuous refactoring.

## 2. Catalog Mechanics Philosophy & Language Adaptation (Preface & Ch. 5)

### The Baby-Steps Scaling & Fallback Rule (Ch. 5.1)

- Every catalog entry presents **safe, minimal baby steps** designed to protect against subtle bugs and avoid debugging sessions.
- **How experienced practitioners use them**: When you know a transformation intimately and can inspect all references at a glance, you may take slightly larger steps (e.g., skipping an intermediate forwarding temp). **However, the very instant a test turns red and the slip is not immediately obvious, revert to the last green commit and replay the move using the catalog's finest-grained baby steps.**

### Language-Agnostic Rules: Static vs. Dynamic Type Systems

Fowler uses JavaScript in the 2nd Edition purely as a widely readable vehicle, emphasizing that refactoring mechanics apply across Java, TypeScript, Python, Go, C#, Ruby, and Rust:

- **Static Types (`Lean on the Compiler`)**: Use the compiler/typechecker to catch broken call sites, missing parameters, and visibility leaks immediately during `Change Function Declaration`, `Move Field`, or `Pull Up Method` - though static checks never eliminate the need for runtime behavioral tests!
- **Dynamic Types**: Compensate for the absence of static type errors by:
  1. Using Kent Beck's indefinite-article type-revealing parameter names (`aPerformance`, `aPlay`, `aCustomer`) to record expected shapes directly in signatures.
  2. Inserting temporary runtime guards (`10.6 Introduce Assertion` or `throw new Error("unexpected type")` inside `isUnknown(arg)` / superclass switch branches) while migrating types, then removing temporary scaffolding once tests pass.

## 3. The Two Hats Protocol (Kent Beck)

Always know which hat you are wearing:

1. **Adding Functionality / Fixing Bugs Hat**:
   - Do not restructure unrelated existing code.
   - Measure progress by adding failing tests and making them pass.
2. **Refactoring Hat**:
   - Do not add new functionality or change observable edge-case behavior.
   - Do not add new feature tests (only adjust test call signatures when an internal module interface intentionally changes via `Change Function Declaration` or `Move Function`).

**Practical Cadence**: Swap hats every 5-10 minutes: try adding a feature -> notice awkward structure -> swap to Refactoring Hat -> apply `Parameterize Function` or `Split Phase` until green -> swap back to Feature Hat -> add the feature in 5 lines -> swap back to Refactoring Hat to tidy names.

## 4. Economic Driver: The Design Stamina Hypothesis

Refactoring is **never** justified on moral or aesthetic grounds ("clean code for art's sake"). Its justification is strictly **economic**: it lets you deliver features faster and fix bugs faster.

- Without continuous refactoring, internal architecture decays cumulatively: every short-term patch makes intent harder to read, causing the next patch to corrupt structure further until velocity collapses.
- High internal design quality creates a compounding platform effect: clean module boundaries reduce how much code you must load into working memory to make a safe change, and reusable building blocks let new domain features snap together rapidly.

## 5. Six Modes of Refactoring Timing

1. **Rule of Three (Don Roberts)**:
   - First time doing something: just write it.
   - Second time doing something similar: wince at the duplication, but do it anyway.
   - Third time doing something similar: refactor (`Extract Function`, `Parameterize Function`, `Pull Up Method`).
2. **Preparatory Refactoring** (*best return on investment*):
   - Right before adding a feature or fixing a bug, inspect existing code and ask: *"How can I restructure this so my incoming change becomes trivial?"*
   - If 3 duplicated blocks all harbor the same bug, consolidate them into one function *first*, then fix the bug once.
3. **Comprehension Refactoring** (*"wiping dirt off the window"*):
   - Whenever you spend 3 minutes figuring out what a variable or 60-line block does, immediately embed that hard-won understanding into the code via `Rename Variable` and `Extract Function`, then run tests to prove your mental model was accurate.
   - Early small cleanups clear surface noise so deeper architectural opportunities become visible.
4. **Litter-Pickup Refactoring** (*Campground Rule*):
   - You understand what the code does, see it is needlessly clumsy, and weigh task focus: if fixing takes 2 minutes, fix it immediately; if it takes an hour, make a small safe improvement now and record the rest in your task notes so every visit leaves the module cleaner without breaking tests.
5. **Opportunistic vs. Planned Refactoring**:
   - Refactoring is woven invisibly into normal feature/bug coding (like writing `if` statements), not isolated into dedicated calendar sprints. Dedicated planned refactoring episodes are needed only when a team neglected refactoring in the past or an area accumulated cross-cutting debt.
   - **VCS Commits Rhythm (Ch. 1 & Ch. 2)**: Commit locally after every green refactoring step so you never lose a working checkpoint, then squash micro-commits into cohesive commits before pushing. Separating large refactorings from feature commits can aid review, though Fowler warns against rigid dogma when tiny opportunistic cleanups are tightly coupled to the feature change.
6. **Long-Term Refactoring (*Branch by Abstraction*)**:
   - For multi-week structural migrations (replacing an ORM/HTTP library, extracting a shared subsystem), avoid long-lived refactoring branches. Introduce an abstraction layer compatible with both old and new implementations, route callers through the abstraction incrementally on trunk while keeping the system live, swap the underlying implementation, and remove the old path.

## 6. Handling Real-World Obstacles

### Published Interfaces & Code Ownership

- When callers live in external repositories or public SDK consumers you cannot edit, direct signature edits break clients.
- Use **Migration Mechanics** (`6.5 Change Function Declaration`): keep the old method as a forwarding shim calling the new method, mark the old method `@deprecated`, and retire it only after a deprecation window. Prefer collective/inner-source code ownership inside a team so internal interfaces can evolve smoothly.

### Feature Branches vs. Continuous Integration (Trunk-Based Development)

- Long-lived feature branches poison refactoring: renaming a widely used symbol on Branch A while Branch B adds new calls to the old name creates silent **semantic merge failures** that text-based `git merge` cannot detect.
- Integrate with mainline frequently (ideally daily via CI + feature flags) and pair CI with self-testing code so semantic conflicts surface immediately.

### YAGNI & Evolutionary Architecture

- Speculative flexibility hooks (10 extra optional parameters, premature strategy hierarchies) add immediate cognitive tax, impair refactoring, and usually guess the wrong axis of future change.
- Build strictly for current known requirements with crisp modular design; introduce flexibility mechanisms up front *only* when retrofitting them later via refactoring would be demonstrably prohibitive.

### Refactoring & Performance (Chapter 2.8)

- Well-factored code can occasionally add minor indirection overhead in the short term, yet makes software **dramatically easier to tune**.
- Most programs spend >90% of runtime inside <10% of their code. Optimizing everything uniformly wastes 90% of effort while degrading maintainability (**Ron Jeffries's Chrysler Payroll lesson**: expert guesses about bottlenecks were 100% wrong until a profiler revealed half the runtime went into repeated string-parsed empty `DateRange` allocations, fixed in 5 minutes via a factory returning a shared immutable empty range).
- **Performance Protocol**:
  1. Write clean, well-factored code first without speculative micro-optimizations (unless building hard real-time systems with strict hardware time budgets).
  2. Profile under realistic load to pinpoint the actual small hotspot functions.
  3. Because refactoring isolated each concern in a small function, apply targeted optimizations in small steps, compiling, testing, and **re-measuring after every step** (revert any optimization that fails to measurably improve the metric).

## 7. Building Self-Testing Code & Legacy Seams (Chapter 4)

Refactoring without fast, self-checking tests turns small slips into exhausting bug hunts. Follow Fowler's complete Chapter 4 testing rules:

### Four-Phase Test Lifecycle & Fresh Fixtures (Ch. 4.3-4.5)

- **Setup - Exercise - Verify - Teardown** (*Arrange - Act - Assert* / *Given - When - Then*):
  - **Fresh Fixtures Over Shared Mutable Fixtures**: Never declare a shared `const asia = new Province(...)` outside `it(...)` blocks and mutate it inside tests - test order dependencies create maddening intermittent failures! Instantiate a fresh baseline inside `beforeEach` so readers gain familiarity with one standard fixture while every test receives an isolated instance.
  - **Focused Verification (One-Assertion Guideline)**: Prefer testing one logical property per `it` block (grouping multiple `expect` calls only when tightly related to one concept) so an early failed assertion does not hide sibling diagnostic clues.
- **Characterization Value-Fill Loop (Ch. 4.3)**:
  When writing tests against existing working code (`expect(asia.profit).toEqual(...)`):
  1. Write an arbitrary placeholder expected value first (e.g., `0`).
  2. Run the test to read the actual value computed by the current code (`230`), and replace `0` with `230` so the test turns green.
  3. **Fault-Injection Proof ("Test the Tests")**: Immediately inject a deliberate bug in the production method (e.g., `* 2`), run the test to **confirm it fails**, and revert the injected fault.

### Boundary Probing vs. Undefined-Contract Crash Tests (Ch. 4.6)

Probe boundaries ("think like an enemy of the code"):

- **Collections**: Empty array `[]` (`0` producers/orders), single-element array, duplicate elements.
- **Numbers**: `0`, negative numbers (`-1`), exact threshold boundaries (`threshold - 1`, `threshold`, `threshold + 1`), NaN/empty-input parse results.
- **Strings & Records**: Empty string `""` (`parseInt("")` returning `NaN`!), numeric string vs. number (`"0"` vs `0`).
- **Assertion Failures vs. Runtime Errors & Deleting Destructive Tests**:
  - Test runners distinguish **failures** (assertion returned false) from **errors** (unexpected exception during setup/exercise, such as passing `producers: ""` where an array is required and crashing with `TypeError: doc.producers.forEach is not a function`).
  - **Crucial Fowler Rule**: If malformed data comes from *untrusted external boundaries* (JSON APIs, user UI), add explicit validation and error tests at that boundary. If the module is fed only by *trusted internal code* within the same codebase, **do not litter every internal module with defensive duplicate checks** (use `10.6 Introduce Assertion` if helpful), and **delete tests that probe undefined crash behavior outside the module's contract before refactoring**! Refactoring must preserve *observable contract behavior*, never accidental crash stack traces on contract-violating inputs.

### Avoiding the Over-Testing Smell (Ch. 4.7)

- Test coverage metrics identify **untested** production branches; they **never** prove a test suite is good.
- Concentrate tests on risk hotspots (complex conditionals, state mutations, boundary math), not trivial pass-through getters.
- **Diagnostic Sign of Over-Testing**: If tests slow you down instead of speeding you up, or you spend far more time updating brittle mock/internal tests than modifying production code, your tests are over-coupled to implementation details - prune redundant tests and test observable behavior at stable module boundaries.

### Legacy Code Without Tests (Michael Feathers's Seam Protocol)

When confronting a large legacy file with zero tests:

1. **Find an existing seam**: Identify the narrowest outer boundary (CLI entrypoint, HTTP handler, pure module export, or batch function) where inputs can be fed and outputs captured without editing complex internals first.
2. **Capture characterization snapshots**: Record current actual outputs across representative + boundary inputs (`scripts/characterization_harness.py`), locking existing behavior as a golden master.
3. **Create minimal test seams only if blocked**: If hardwired clocks (`Date.now()`), random generators, or direct DB/network calls block testing, perform **one** surgical, mechanical seam extraction (`6.5 Change Function Declaration` / `11.6 Replace Query with Parameter` with default parameter `clock = SystemClock`) to inject a deterministic stub, verify with fault injection, and only then begin structural refactoring.
4. **Refactor incrementally along hot paths**: Apply the Campground Rule to the high-churn modules you actively touch rather than freezing delivery for a total codebase rewrite.
