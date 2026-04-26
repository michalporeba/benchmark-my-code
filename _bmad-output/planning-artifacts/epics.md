---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories']
inputDocuments: ['docs/project-overview.md', 'docs/architecture.md', 'plans/phase_2_planning.md', 'plans/phase_3_planning.md']
---

# benchmark-my-code - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for benchmark-my-code, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Robust statistical measurement using medians over means for execution times.
FR2: Batch execution of benchmarks with warm-up cycles and 1% stability convergence detection.
FR3: Ad-hoc benchmarking using a @benchit decorator and global registry.
FR4: Pluggable output layer supporting CLI (ASCII/Rich), HTML (Notebooks), JSON, and Pandas DataFrames.
FR5: Challenge-based benchmarking using a @challenge decorator with signature validation.
FR6: Adaptive timeouts based on hidden reference implementation execution.
FR7: Staged pedagogical feedback mapping failure types to student-friendly hints.
FR8: Decoupled memory profiling using tracemalloc.

### NonFunctional Requirements

NFR1: Zero-dependency core engine (optional dependencies for visualization only).
NFR2: Mutation safety through deep-copying all input variants.
NFR3: Strict separation between timing and memory profiling passes.
NFR4: High test coverage with red-green-refactor discipline.
NFR5: Support for Python 3.12+ (current 3.13.7).
NFR6: Statistical robustness against system jitter and JIT optimizations.

### Additional Requirements

AR1: Improve memory efficiency of statistical processing by avoiding massive temporary list creation in Function.median_time.
AR2: Replace ThreadPoolExecutor in the inner loop with a more efficient timeout mechanism to reduce per-execution overhead.
AR3: Fix "Ghost Thread" leak by ensuring timed-out executions are properly handled or isolated.
AR4: Optimize deepcopy overhead by allowing users to opt-out or by using more efficient cloning for immutable/large data.
AR5: Resolve BenchmarkResult staleness by making statistics lazy-loaded or updating on demand.
AR6: Consolidate optional dependency imports (rich, pandas) to reduce overhead.
AR7: Update status reporting to distinguish between "UNINITIALIZED" and "PASS".
AR8: Use context managers for tracemalloc and ensure gc.collect() between iterations to maintain profiling hygiene.
AR9: Improve efficiency of statistical calculations (median) to avoid O(N log N) bottlenecks at scale.

### UX Design Requirements

UX-DR1: Terminal ASCII tables must be legible and automatically scale based on function name/variant length.
UX-DR2: Jupyter Notebook output must use semantic colors for pass/fail states.
UX-DR3: Pedagogical hints must be displayed clearly below the results table.

### FR Coverage Map

FR1: Epic 1 - Robust statistical measurement using medians.
FR2: Epic 1 - Batch execution and convergence detection.
FR3: Epic 2 - @benchit decorator and ad-hoc registry.
FR4: Epic 3 - Pluggable output (CLI, HTML, JSON, Pandas).
FR5: Epic 4 - @challenge decorator and signature validation.
FR6: Epic 4 - Adaptive hardware-aware timeouts.
FR7: Epic 4 - Staged pedagogical feedback engine.
FR8: Epic 1 - Decoupled memory profiling with tracemalloc.

## Epic List

### Epic 1: Hardened Core Engine
Deliver a statistically robust, memory-efficient, and leak-proof execution engine. Users will get reliable benchmarks that are immune to OS jitter and resource leaks.
**FRs covered:** FR1, FR2, FR8

### Epic 2: Zero-Setup Declarative Benchmarking
Transform the library from an imperative tool into a declarative framework. Developers can benchmark code with minimal boilerplate by relying on intelligent argument matching and an automated CLI runner.
**FRs covered:** FR3

### Epic 3: Multi-Platform Reporting & Analysis
Deliver actionable insights across CLI, Notebooks, and Data science tools. Users can visualize and export results in their preferred workflow without unnecessary import overhead.
**FRs covered:** FR4

### Epic 4: Automated Pedagogical Challenges
Enable the creation of structured coding exercises with hardware-aware feedback. Educators can automate student code validation with intelligent hints based on performance ceilings.
**FRs covered:** FR5, FR6, FR7

## Epic 1: Hardened Core Engine

Deliver a statistically robust, memory-efficient, and leak-proof execution engine. Users will get reliable benchmarks that are immune to OS jitter and resource leaks.

### Story 1.1: Efficient Median Selection & Stat Hygiene

As an engine developer,
I want to use a selection-based algorithm for medians and avoid temporary list allocations,
So that the engine can process thousands of data points without O(N log N) sorting overhead or memory spikes.

**Acceptance Criteria:**

**Given** execution times stored in `array.array`
**When** `median_time()` is called
**Then** the median is calculated using a selection algorithm (e.g., quickselect) that operates with O(N) average time complexity
**And** no temporary Python lists are created by extending the `array.array` contents during calculation

### Story 1.2: Single-Worker Executor with Stall Detection

As a notebook user,
I want my benchmarks to run in a single persistent background thread that detects hangs,
So that I don't accidentally leak multiple "ghost" threads if my code infinite loops, and I know when a restart is required.

**Acceptance Criteria:**

**Given** the benchmarking engine is initialized
**When** a benchmark is started
**Then** all executions are routed through a single, persistent background worker thread
**And** if an execution times out, the worker is marked as "Stalled" and refuses further work
**And** the engine provides a specific error message advising a kernel/process restart when in a stalled state

### Story 1.3: Hygienic & Decoupled Memory Pass

As an engine developer,
I want to run memory profiling as a strictly separate pass with explicit lifecycle management,
So that instrumentation overhead doesn't skew timing results and memory traces are isolated.

**Acceptance Criteria:**

**Given** a benchmark with multiple variants
**When** the memory pass is executed
**Then** it runs separately from the timing pass and uses a context manager for `tracemalloc`
**And** `gc.collect()` and `tracemalloc.clear_traces()` are called between each variant iteration to prevent cross-contamination

## Epic 2: Zero-Setup Declarative Benchmarking

Transform the library from an imperative tool into a declarative framework. Developers can benchmark code with minimal boilerplate by relying on intelligent argument matching and an automated CLI runner.

### Story 2.1: The `benchit` CLI Runner & Discovery

As a developer,
I want to execute benchmarks via a command-line tool (e.g., `benchit my_file.py`) without writing `run_benchmarks()` in my code,
So that my source files remain clean and focused solely on the implementations.

**Acceptance Criteria:**

**Given** a Python file containing functions decorated with `@benchit`
**When** the `benchit` CLI command is run against the file
**Then** the engine automatically discovers all decorated functions using AST or module introspection
**And** it executes them without executing top-level scripts or requiring explicit entry-point boilerplate
**And** it provides explicit status reporting, clearly differentiating "PENDING" from "PASS"

### Story 2.2: Pytest-Style Parametrization via Name Matching

As a developer,
I want the engine to automatically map globally defined iterables to my benchmark function arguments based on parameter names,
So that I don't have to manually construct complex dictionaries or loops to test multiple variants.

**Acceptance Criteria:**

**Given** a function `def sort_alg(data):` and a global iterable named `data`
**When** the benchmark executes
**Then** the engine inspects the function signature and automatically injects elements from the `data` iterable as variants
**And** if `data` is a generator or yields a tuple of arguments, it is treated as multiple discrete use cases
**And** the engine performs a smart `deepcopy` (or allows an opt-out via the decorator) to ensure mutation safety without undue overhead

### Story 2.3: Directed Acyclic Graph (DAG) Parameter Resolution

As a power user,
I want the engine to resolve benchmark parameters by finding functions that provide those parameters (like pytest fixtures),
So that I can build complex, dynamic test cases simply by matching function names to argument names.

**Acceptance Criteria:**

**Given** a benchmark function `def test_func(large_array):` and a separate parameter-provider function `def large_array(): yield [1,2,3]`
**When** the benchmark executes
**Then** the engine constructs a DAG to identify `large_array` as the data source for the benchmark's argument
**And** it executes the provider function to supply the variants for the benchmark
**And** it gracefully handles missing dependencies with a clear, informative error

## Epic 3: Multi-Platform Reporting & Analysis

Deliver actionable insights across CLI, Notebooks, and Data science tools. Users can visualize and export results in their preferred workflow without unnecessary import overhead.

### Story 3.1: Lazy-Loaded Statistics

As a developer,
I want the `BenchmarkResult` to pull the latest stats from the model only when requested,
So that my interactive Notebook results are never stale if a benchmark is still running or gets updated.

**Acceptance Criteria:**

**Given** a `BenchmarkResult` object
**When** `stats` or formatters (`__str__`, `_repr_html_`) are accessed
**Then** it dynamically generates the latest statistics from the underlying `Benchmark` model rather than relying on a static `__init__` snapshot

### Story 3.2: Overhead-Free Optional Dependencies

As a performance-conscious user,
I want the reporting layer to only attempt to import large libraries (`rich`, `pandas`) when their specific export methods are called,
So that my core benchmarking script doesn't suffer from filesystem overhead or import delays.

**Acceptance Criteria:**

**Given** a benchmark script running in a minimal environment
**When** `run_benchmarks()` is called with standard ASCII output
**Then** the engine does not attempt to import `rich` or `pandas` at the module level or during standard terminal output generation

## Epic 4: Automated Pedagogical Challenges

Enable the creation of structured coding exercises with hardware-aware feedback. Educators can automate student code validation with intelligent hints based on performance ceilings.

### Story 4.1: Adaptive Hardware-Aware Timeouts

As an educator,
I want the engine to secretly run a reference implementation to establish a hardware-specific baseline time,
So that my student timeouts are fair and adaptive, regardless of whether they run on a slow laptop or a fast server.

**Acceptance Criteria:**

**Given** a `@challenge` that defines a `reference` function and a `timeout_multiplier`
**When** the challenge is executed
**Then** the engine securely executes the reference function first
**And** it sets the absolute timeout for the student's code to `(reference_time * timeout_multiplier)`

### Story 4.2: Staged Pedagogical Hint Engine

As a student,
I want to receive specific, actionable hints when my code fails on certain edge cases or large datasets,
So that I understand *why* my code failed, rather than just seeing a generic timeout or failure message.

**Acceptance Criteria:**

**Given** a `@challenge` with defined stages (e.g., "Small Data", "Large Data", "Edge Cases") and associated hints
**When** my code fails or times out during a specific stage
**Then** the output automatically displays the corresponding pedagogical hint from the challenge configuration (addressing UX-DR3)
