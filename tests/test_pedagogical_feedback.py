import pytest
import time
from benchmark_my_code import challenge, Challenge, run_benchmarks, clear_registry, FailureType

def setup_function():
    clear_registry()

def test_staged_feedback_correctness():
    # 1. Educator defines a challenge with stages and hints
    my_chall = Challenge(
        name="Fibonacci",
        parameters=["n"],
        stages={
            "Basic": {"Small": (0,)},
            "Scale": {"Large": (30,)}
        },
        reference=lambda n: 0 if n == 0 else 1, # Simplified ref
        hints={
            ("Basic", FailureType.CORRECTNESS): "Check your base cases!",
            ("Scale", FailureType.TIMEOUT): "Try memoization!"
        }
    )
    
    # 2. Student solution that fails basic correctness
    @challenge(my_chall)
    def student_solution(n):
        return 999 # Wrong!
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    
    # Check that it stopped and provided the correct hint
    assert "Check your base cases!" in result.hints
    # Since it failed Basic, it shouldn't have run Scale
    assert result.get_function('Reference_Fibonacci').variant_count == 1

def test_staged_feedback_timeout():
    def slow_ref(n):
        return n
        
    my_chall = Challenge(
        name="Fast Challenge",
        parameters=["n"],
        stages={
            "Basic": {"Small": (1,)},
            "Scale": {"Large": (100,)}
        },
        reference=slow_ref,
        timeout_multiplier=0.1, # Impossible multiplier
        hints={
            ("Scale", FailureType.TIMEOUT): "Your solution is too slow for large inputs."
        }
    )
    
    @challenge(my_chall)
    def student_solution(n):
        time.sleep(0.01) # Wait slightly
        return n
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    assert "Your solution is too slow for large inputs." in result.hints
