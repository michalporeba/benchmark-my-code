# Architecture Overview

This document outlines the architectural design and design philosophy of `benchmark-my-code`.

## Executive Summary
`benchmark-my-code` is a stateless Python library designed for educational benchmarking. It prioritizes reliability and statistical stability over raw execution speed, making it ideal for pedagogical feedback in coding challenges.

## Technology Stack
- **Language**: Python 3.12+
- **Build System**: Hatchling
- **Profiling**: Standard Library (`tracemalloc`, `concurrent.futures`, `time.perf_counter_ns`)
- **Metadata Analysis**: Standard Library (`ast`, `inspect`)
- **CLI Visualization**: Rich (optional)

## Architecture Patterns
The library follows a **Layered Architecture** with a clear separation of concerns:

1.  **API Layer (`api.py`)**: Handles user registration via decorators (`@benchit`, `@challenge`) and provides the main entry point (`run_benchmarks`). It also performs static validation of code constraints.
2.  **Orchestration Layer (`orchestrator.py`)**: The engine that drives execution. It implements statistical safety measures like warmups, batch execution, and early convergence checks.
3.  **Model Layer (`model.py`)**: Stateless data structures that hold execution results, benchmark metadata, and challenge configurations.
4.  **Presentation Layer (`result.py`)**: Transforms raw benchmark data into human-readable formats (ASCII tables for CLI, HTML for Notebooks).

## Data Architecture
The data flow is unidirectional:
`User Code` → `Decorators` → `Orchestrator` → `Benchmark Model` → `BenchmarkResult`.

### Key Models
- **`Function`**: Encapsulates a single function and its execution history across variants.
- **`Benchmark`**: A collection of `Function` objects.
- **`Challenge`**: Metadata for structured pedagogical exercises (hints, reference implementations, stages).

## Statistical Design Decisions (ADRs)
- **ADR 1: Reliable Timing**: Uses medians over means to drop outliers and a 1% rolling convergence threshold for early exit.
- **ADR 2: Decoupled Profiling**: Time and memory profiling are run in separate passes to avoid instrumentation overhead skewing timing data.
- **ADR 3: Mutation Safety**: Always performs a `deepcopy` of input variants before each execution to prevent cross-contamination.

## Development Workflow
The project follows a strict **Planner -> Implementer -> Reviewer** role-based workflow for all features, managed by AI agents through Gemini CLI.
