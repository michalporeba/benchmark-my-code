# Project Overview

`benchmark-my-code` is a lightweight, reliable Python benchmarking engine designed for educational environments.

## Purpose
The library allows developers and students to measure the performance (timing and memory) of their code while providing pedagogical feedback through structured "Challenges." It is built to be statistically robust against system noise and JIT optimizations.

## Core Features
- **Statistical Stability**: Medians over means, warmup executions, and early convergence at 1% stability.
- **Pedagogical Feedback**: Challenge mode with hints, reference implementations, and staged validation.
- **Fairness & Safety**: Deep-copying inputs to prevent mutation side-effects and AST-based algorithmic constraints.
- **Zero-Dependency Core**: Lightweight engine with optional rich visualizations.
- **Developer Experience**: Simple decorators (`@benchit`, `@challenge`) and multiple output formats (CLI, Notebook).

## Repository Status
- **Phase**: 1 (Foundation & Tooling) / 2 (Core Engine).
- **Architecture**: Layered, stateless library.
- **Package Management**: `uv`.
- **Testing**: `pytest` (high coverage).

## Documentation Links
- [Architecture Overview](./architecture.md)
- [API Contracts](./api-contracts.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)
