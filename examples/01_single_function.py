import logging
import sys
import os

# Add the project root to the python path to run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from benchmark_my_code import bench

# Setup simple logging to see what the engine is doing
logging.basicConfig(level=logging.INFO, format="%(message)s")

def sum_to_n(n):
    """A simple function that calculates the sum from 1 to N."""
    total = 0
    for i in range(n + 1):
        total += i
    return total

if __name__ == '__main__':
    print("--- Running Benchmark for a Single Function ---")
    
    # We want to benchmark sum_to_n for several variants (different values of N)
    variants = [(10,), (100,), (1000,)]
    
    result = bench(sum_to_n, variants, max_executions=50)
    
    # Simple manual terminal output for DX showcase (will be improved in Phase 2D)
    print("\n--- Results ---")
    func_stats = result.get_function('sum_to_n')
    print(f"Function: {func_stats.name} (Total Executions: {func_stats.executions})")
    
    # _executions is an internal dict, but we'll access it to print the variants
    for variant in func_stats._executions:
        count = len(func_stats.get_executions(variant))
        total_t = func_stats.total_time(variant)
        print(f"  Variant {variant}: ran {count} times, total time = {total_t:.5f}s")
