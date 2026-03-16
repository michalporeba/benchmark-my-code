import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from benchmark_my_code import bench

logging.basicConfig(level=logging.INFO, format="%(message)s")

def helper_function(x):
    """A helper function that we DO NOT want to benchmark."""
    return x * 2

def complex_calculation(n):
    """The function we ACTUALLY want to benchmark."""
    result = 0
    for i in range(n):
        result += helper_function(i)
    return result

def another_unused_function():
    pass

if __name__ == '__main__':
    print("--- Running Benchmark for One Specific Function Among Many ---")
    
    variants = [(50,), (500,)]
    
    # We only pass complex_calculation to the bench function
    result = bench(complex_calculation, variants, max_executions=25)
    
    print("\n--- Results ---")
    func_stats = result.get_function('complex_calculation')
    print(f"Function: {func_stats.name}")
    for variant in func_stats._executions:
        count = len(func_stats.get_executions(variant))
        print(f"  Variant {variant}: ran {count} times, min time = {func_stats.min_time(variant):.5f}s, max = {func_stats.max_time(variant):.5f}s")
