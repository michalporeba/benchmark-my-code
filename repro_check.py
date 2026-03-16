import sys
import os
import time
import logging

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from benchmark_my_code import bench, Benchmark

# Setup logging to see output
logging.basicConfig(level=logging.INFO)

def test_func(x):
    # Simulate some work
    time.sleep(0.001)
    return x * 2

def test_parameterless():
    time.sleep(0.001)

try:
    print("Testing parameterless function...")
    benchmark = bench(test_parameterless, max_executions=15)
    print(f"Parameterless function benchmarked. Executions: {benchmark.get_function('test_parameterless').executions}")

    print("\nTesting function with parameters...")
    # This should now work with the fixes
    benchmark = bench(test_func, [1, 2, 3], max_executions=15)
    func = benchmark.get_function('test_func')
    print(f"Parameterized function benchmarked. Executions: {func.executions}")
    for variant in func._executions:
        print(f"Variant '{variant}': {len(func.get_executions(variant))} executions")

except Exception as e:
    print(f"\nCaught unexpected exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
