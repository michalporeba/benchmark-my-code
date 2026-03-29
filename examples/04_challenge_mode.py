import logging
import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from benchmark_my_code import challenge, Challenge, run_benchmarks, ForbiddenCallError

# Setup logging
logging.basicConfig(level=logging.WARNING)

# 1. Educator defines a "Manual Sort" challenge
# We provide a reference implementation and BAN 'sorted' and 'list.sort'
# We also name the variants for better readability
manual_sort_challenge = Challenge(
    name="Manual Bubble Sort",
    parameters=["data"],
    variants={
        "Small Random": (random.sample(range(100), 5),),
        "Medium Random": (random.sample(range(100), 10),),
        "Large Random": (random.sample(range(100), 20),),
    },
    banned_calls=["sorted", "sort"],
    reference=lambda data: sorted(data)
)

# 2. Student attempts a solution (the "Mentor" catches the shortcut)
try:
    print("--- Attempting Shortcut (Forbidden) ---")
    @challenge(manual_sort_challenge)
    def lazy_solution(data):
        return sorted(data) # This will raise ForbiddenCallError immediately
except ForbiddenCallError as e:
    print(f"Caught expected error: {e}\n")

# 3. Student writes a proper solution
@challenge(manual_sort_challenge)
def proper_bubble_sort(data):
    """A simple bubble sort implementation."""
    n = len(data)
    # We work on a copy because orchestrator deep-copies for us anyway, 
    # but it's good practice.
    arr = list(data) 
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

if __name__ == '__main__':
    print("--- Running Advanced Challenge Mode ---")
    # run_benchmarks() will run the student solution AND the hidden reference
    run_benchmarks(validate=True)
