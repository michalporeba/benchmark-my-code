# Plan: Break down Phase 3 into Smaller Features

## Objective
Update the high-level `PLANS.md` roadmap to break "Phase 3: Educational Features" into smaller, manageable chunks, and create detailed feature plan files in the `plans/` directory.

## 1. Update `PLANS.md`
Replace the old Phase 3 section with:

```markdown
## Phase 3: Educational Features
- [ ] **3A: Challenge API & Validation**: `@challenge` decorator, registry, and `inspect`-based signature checking. *See: `plans/03a-challenge-api.md`*
- [ ] **3B: Reference Baselines & Adaptive Timeouts**: Executing hidden reference functions to set a performance ceiling. *See: `plans/03b-adaptive-timeouts.md`*
- [ ] **3C: Staged Feedback & Guidance**: Mapping failures (timeout, correctness, Big-O) to specific student-friendly messages. *See: `plans/03c-pedagogical-feedback.md`*
- [ ] **3D: Adaptive Memory Profiling**: `tracemalloc` integration that only samples at key intervals to sketch the curve. *See: `plans/03d-adaptive-memory.md`*
```

## 2. Create `plans/03a-challenge-api.md`
```markdown
# Plan: 03A - Challenge API & Validation
**Objective:** Implement the `@challenge` decorator to register student code against a predefined Challenge object. Use the `inspect` module to validate that the student's function signature matches the challenge's requirements before execution.
```

## 3. Create `plans/03b-adaptive-timeouts.md`
```markdown
# Plan: 03B - Reference Baselines & Adaptive Timeouts
**Objective:** Logic to execute the hidden reference implementation secretly to establish a hardware-specific baseline. Set absolute timeouts for student code as a multiple of this baseline (e.g., 10x reference time).
```

## 4. Create `plans/03c-pedagogical-feedback.md`
```markdown
# Plan: 03C - Staged Feedback & Guidance
**Objective:** Define "stages" within a Challenge (Small, Large, Edge Cases). Implement the feedback engine that maps specific failure types (e.g., "Timed out on large variant") to pedagogical hints.
```

## 5. Create `plans/03d-adaptive-memory.md`
```markdown
# Plan: 03D - Adaptive Memory Profiling
**Objective:** Integrate `tracemalloc`. Implement the logic to decouple memory and time profiling, sampling memory at strategic boundaries (start, end, and specific intervals) to sketch a Big-O memory trend without significant time overhead.
```

## Verification
- Verify `PLANS.md` is updated.
- Verify `plans/03a-challenge-api.md`, `plans/03b-adaptive-timeouts.md`, `plans/03c-pedagogical-feedback.md`, and `plans/03d-adaptive-memory.md` exist in the workspace.