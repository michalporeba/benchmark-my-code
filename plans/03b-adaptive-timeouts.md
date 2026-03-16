# Plan: 03B - Reference Baselines & Adaptive Timeouts

## Objective
Logic to execute the hidden reference implementation secretly to establish a hardware-specific baseline. Set absolute timeouts for student code as a multiple of this baseline (e.g., 10x reference time).

## Context
Timeouts are essential to prevent infinite loops, but absolute time limits (e.g., "5 seconds") are unfair to users on older machines. We should measure the reference implementation *on the same machine* and use its time as a baseline.

## Steps
1. **Reference Execution**:
   - Before benchmarking the student's code, the orchestrator runs the hidden reference function on the same variants.
2. **Calculating Relative Timeouts**:
   - Record the time taken by the reference ($T_{ref}$).
   - Set the timeout for the student's code to $T_{ref} \times K$ (where $K$ is a multiplier like 10 or 20).
3. **Integration with Orchestrator**:
   - Update the batch execution loop to respect these adaptive timeouts.
4. **Tests**:
   - Mock a slow and a fast reference implementation and verify that the student's code timeout scales accordingly.
