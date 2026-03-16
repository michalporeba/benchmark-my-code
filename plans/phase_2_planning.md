# Plan: Break down Phase 2 into Smaller Features

## Objective
Update the high-level `PLANS.md` roadmap to break "Phase 2" into smaller, manageable chunks, and create detailed feature plan files in the `plans/` directory.

## 1. Update `PLANS.md`
Replace the old Phase 2 section with:

```markdown
## Phase 2: The Core Engine
- [ ] **2A: Core Statistics & Timers**: Implement robust measurement (medians over means, tracking min/max). *See: `plans/02a-core-statistics.md`*
- [ ] **2B: Batch Execution & Convergence**: Implement warmups, batch chunking, and 1% stability convergence. *See: `plans/02b-batch-execution.md`*
- [ ] **2C: Ad-Hoc Mode API**: Create `@benchit` decorators, handle multiple functions, and deep-copy inputs. *See: `plans/02c-adhoc-mode.md`*
- [ ] **2D: Pluggable Output**: Build `BenchmarkResult` object, terminal CLI tables, and JSON export. *See: `plans/02d-pluggable-output.md`*
```

## 2. Create `plans/02a-core-statistics.md`
```markdown
# Plan: 02A - Core Statistics & Timers
**Objective:** Upgrade `model.py` to use `statistics.median` instead of arithmetic means, ensuring robust handling of OS jitter. Verify timer precision using `time.perf_counter_ns()`.
```

## 3. Create `plans/02b-batch-execution.md`
```markdown
# Plan: 02B - Batch Execution & Convergence
**Objective:** Modify `orchestrator.py` to run functions in defined batches, discarding the first batch as a warmup. Implement the 1% median convergence check to stop early.
```

## 4. Create `plans/02c-adhoc-mode.md`
```markdown
# Plan: 02C - Ad-Hoc Mode API
**Objective:** Build the `@benchit` decorator and global registry in `__init__.py`. Implement deep-copying of inputs within the orchestrator to prevent mutation side-effects. Add basic `validate=True` logic to ensure all functions return identical results.
```

## 5. Create `plans/02d-pluggable-output.md`
```markdown
# Plan: 02D - Pluggable Output
**Objective:** Define a rich `BenchmarkResult` object. Implement a clean terminal ASCII table representation. Add a `.to_dict()` method for simple JSON serialization.
```

## Verification
- Verify `PLANS.md` is updated.
- Verify `plans/02a-core-statistics.md`, `plans/02b-batch-execution.md`, `plans/02c-adhoc-mode.md`, and `plans/02d-pluggable-output.md` exist in the workspace.