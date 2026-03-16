# Plan: 03A - Challenge API & Validation

## Objective
Implement the `@challenge` decorator to register student code against a predefined Challenge object. Use the `inspect` module to validate that the student's function signature matches the challenge's requirements before execution.

## Context
In "Challenge Mode", students implement a function that must match a specific signature (e.g., `def my_sort(input_list):`). We need a decorator that links their function to a challenge and a mechanism to validate their signature *before* running any benchmarks.

## Steps
1. **The `@challenge` Decorator**:
   - Create a decorator that accepts a `Challenge` object (which defines variants, references, and expected signature).
   - Register the decorated function into a challenge-specific runner.
2. **Signature Validation**:
   - Use `inspect.signature()` to compare the student's function with the required signature.
   - If it doesn't match (wrong number of arguments, wrong names if specified), throw a helpful error that includes a "Stub" for them to copy.
3. **Registry**:
   - Maintain a registry of challenges so the orchestrator knows which functions belong to which challenge.
4. **Tests**:
   - Test that the decorator correctly registers the function.
   - Test that signature validation catches common mistakes (missing parameters, too many parameters) and provides the correct stub in the error message.
