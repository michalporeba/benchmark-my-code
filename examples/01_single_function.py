import logging
import sys
import os

# Add the project root to the python path to run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from benchmark_my_code import benchit, run_benchmarks

# Setup simple logging to see what the engine is doing
logging.basicConfig(level=logging.WARNING)

@benchit
def sum_to_n(n):
    """A simple function that calculates the sum from 1 to N."""
    total = 0
    for i in range(n + 1):
        total += i
    return total

@benchit
def memory_heavy_sum(n):
    """A version that allocates a list (memory heavy)."""
    return sum([i for i in range(n + 1)])

if __name__ == '__main__':
    print("--- Running Modern Benchmark DX ---")
    
    # Run benchmarks for all decorated functions
    run_benchmarks(
        variants={
            "Small": (10,),
            "Medium": (1000,),
            "Large": (100000,)
        },
        max_executions=50
    )
