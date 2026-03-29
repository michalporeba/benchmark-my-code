import logging
import sys
import os
import random
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from benchmark_my_code import challenge, Challenge, run_benchmarks, FailureType

# Setup logging
logging.basicConfig(level=logging.WARNING)

# 1. Educator defines a challenge with multiple stages
fib_challenge = Challenge(
    name="Recursive Fibonacci",
    parameters=["n"],
    stages={
        "Basic": {"Small": (10,)},
        "Scale": {"Large": (35,)} # This will be slow without memoization
    },
    reference=lambda n: 55 if n == 10 else 9227465, # Simple mocked ref
    hints={
        ("Basic", FailureType.CORRECTNESS): "Your Fibonacci math seems wrong. Did you get the base cases?",
        ("Scale", FailureType.TIMEOUT): "It works! But it's too slow for larger numbers. Have you tried memoization?"
    },
    timeout_multiplier=2.0 # Strict timing for this one
)

# 2. Student writes a slow recursive solution
@challenge(fib_challenge)
def recursive_fib(n):
    if n <= 1: return n
    return recursive_fib(n-1) + recursive_fib(n-2)

if __name__ == '__main__':
    print("--- Running Staged Challenge Mode ---")
    # run_benchmarks() will run Basic, then fail on Scale and provide the hint
    run_benchmarks(validate=True)
