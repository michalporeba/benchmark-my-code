import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from benchmark_my_code import benchit, run_benchmarks

# In this example, we keep logging at WARNING so we only see the final summary.
logging.basicConfig(level=logging.WARNING, format="%(message)s")

@benchit
def reverse_string_pythonic(s):
    """Implementation 1: Using slicing."""
    return s[::-1]

@benchit
def reverse_string_loop(s):
    """Implementation 2: Using a for loop."""
    result = ""
    for char in s:
        result = char + result
    return result

@benchit
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
    
    # We now just call run_benchmarks and it automatically picks up the decorated functions.
    # We also pass validate=True to ensure they all actually produce the same reversed string!
    # By default, it will cleanly print the results to the terminal.
    run_benchmarks(variants=variants, max_executions=50, validate=True)

