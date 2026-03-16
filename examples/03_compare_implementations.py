import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from benchmark_my_code import bench

# In this example, we keep logging at WARNING so we only see the final summary.
logging.basicConfig(level=logging.WARNING, format="%(message)s")

def reverse_string_pythonic(s):
    """Implementation 1: Using slicing."""
    return s[::-1]

def reverse_string_loop(s):
    """Implementation 2: Using a for loop."""
    result = ""
    for char in s:
        result = char + result
    return result

def reverse_string_list(s):
    """Implementation 3: Using list reverse."""
    chars = list(s)
    chars.reverse()
    return "".join(chars)

if __name__ == '__main__':
    print("--- Comparing Multiple Implementations ---")
    
    # Create a long string to reverse
    long_string = "A" * 1000
    variants = [(long_string,)]
    
    # Currently, `bench` only accepts a single function.
    # So we have to call it multiple times and collect the results.
    # (Phase 2C will introduce `@benchit` decorators to solve this DX friction!)
    benchmarks = []
    benchmarks.append(bench(reverse_string_pythonic, variants, max_executions=50))
    benchmarks.append(bench(reverse_string_loop, variants, max_executions=50))
    benchmarks.append(bench(reverse_string_list, variants, max_executions=50))
    
    print("\n--- Results Summary ---")
    print(f"{'Implementation':<30} | {'Executions':<12} | {'Min Time (s)':<15}")
    print("-" * 65)
    
    for b in benchmarks:
        for func in b.functions:
            variant = "('A' * 1000,)"
            # It might be saved as a string representation of the tuple
            # We can just iterate over whatever variants it has
            for v in func._executions:
                min_t = func.min_time(v)
                count = len(func.get_executions(v))
                print(f"{func.name:<30} | {count:<12} | {min_t:.6f}")
