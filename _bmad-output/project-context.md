---
project_name: 'benchmark-my-code'
user_name: 'Michał'
date: '2026-04-25'
sections_completed: ['technology_stack', 'language_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']
status: 'complete'
rule_count: 24
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python**: >= 3.12 (Current: 3.13.7)
- **Package Manager**: `uv` (STRICT MANDATE)
- **Testing**: `pytest` (Current: 9.0.2)
- **Build System**: `hatchling`
- **Key Dependencies**: `rich` >= 13.0.0 (Optional CLI), `tracemalloc`, `concurrent.futures`, `ast`, `inspect` (StdLib)
- **Linting/Types**: `ruff`, `mypy`

## Critical Implementation Rules

### 🐍 Language-Specific Rules (Python)
- **Self-Documenting Core**: Prioritize expressive naming and strict typing over comments. Use `TypedDict`, `Protocol`, and `NewType` to make data structures self-explanatory.
- **Public API Docstrings**: Public-facing functions (e.g., `@benchit`, `@challenge`) should have concise docstrings for intent and examples. Internal logic should avoid docstrings unless the "Why" is complex.
- **Execution Isolation**: Core engine logic must remain strictly synchronous. Use `ThreadPoolExecutor` only for timeout monitoring. Support user `async` functions by wrapping them in `asyncio.run()` within the execution context.
- **Metaprogramming Layer**: Isolate `ast` and `inspect` logic in a dedicated "analysis" module for pre-execution validation.
- **Explicit Error Triage**: Zero unhandled exceptions. Distinguish between Engine Errors (system failures) and Benchmark Failures (user code crashes).
- **Profiling Hygiene**: Use Context Managers for `tracemalloc`. Mandatory `gc.collect()` and `tracemalloc.clear_traces()` between variant iterations.
- **Input Integrity**: Strict use of `copy.deepcopy` for variant arguments. Use `inspect.signature` to verify mapping to target parameters.

### 🧪 Testing Rules
- **Strict Red-Green-Refactor (RGR)**: Failing test first, minimal green implementation, then refactor.
- **Memory Profiling (Trend-Based)**: Avoid byte-perfect assertions. Use Safety Envelopes and Trend Assertions (e.g., no linear growth for O(1) ops).
- **Non-Determinism**: Mock `time.perf_counter` for logic tests. Use statistical aggregation (n=100) and relative thresholds for performance assertions.
- **Verification**: Use deterministic math workloads to verify convergence (1% rule) and median calculations.
- **CI Stability**: Every test must pass 100/100 times in a controlled environment to be accepted.

### ✨ Code Quality & Style Rules
- **Naming**: `snake_case` for modules/functions/vars, `PascalCase` for classes, `_prefix` for private members.
- **Type Safety**: Mandatory `mypy --strict`. 100% type coverage for `api.py` and `orchestrator.py`. No `Any` in public signatures.
- **Tooling**: `ruff` for linting, formatting, and import sorting. `mypy` for structural validation.
- **Architecture**: Strict separation between Analysis, Orchestration, and Presentation layers.

### 🚀 Development Workflow Rules
- **Tactical vs. Strategic**:
    - **Quick Dev**: Authorized for leaf-node fixes or CLI additions. Must still pass the full "Trust Suite" (ruff, mypy, pytest) in the same turn.
    - **Formal Planning**: Mandatory for Core Engine (`orchestrator.py`) or API Contract (`api.py`) changes.
- **The "One-Sentence" Test**: If a change's impact cannot be described in one sentence, it requires a formal plan.
- **Roles**: Follow the Planner -> Implementer -> Reviewer cycle for all non-trivial tasks.

## 🛑 Critical Don't-Miss Rules (Anti-Patterns)

- **❌ Top-Level Heavy Imports**: Never import heavy libs (pandas, matplotlib) at the module level. Use delayed imports.
- **❌ Profile Mixing**: Never run time and memory profiling simultaneously. Timing stability first, then a separate memory pass.
- **❌ Mutation Pollution**: Never pass variant data directly. **Always `deepcopy` first.**
- **❌ Persistence in Core**: Never add DB or stateful history logic to the core engine. Keep it stateless.
- **❌ Silent Failures**: Never use bare `except: pass`. Every crash is a data point.
- **❌ Absolute Precision**: Never write tests depending on microsecond or byte-level precision across platforms.

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code.
- Follow ALL rules exactly as documented.
- When in doubt, prefer the more restrictive option.
- Update this file if new patterns or architectural decisions emerge.

**For Humans:**
- Keep this file lean and focused on agent needs.
- Update when the technology stack or ADRs change.
- Review quarterly to remove rules that have become common knowledge.

Last Updated: 2026-04-25
