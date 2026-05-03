import pytest
import time
from benchmark_my_code import challenge, Challenge, run_benchmarks, clear_registry, FailureType, reset

def setup_function():
    clear_registry()
    reset()

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
    
    # Check that it stopped and provided the correct hint with context
    assert len(result.hints) == 1
    hint = result.hints[0]
    assert hint['message'] == "Check your base cases!"
    assert hint['stage'] == "Basic"
    assert hint['variant'] == "Small"

def test_smart_hint_lookup_fallbacks():
    my_chall = Challenge(
        name="Fallback Test",
        parameters=["n"],
        stages={"S1": {"v1": 1}},
        reference=lambda n: n,
        hints={
            (None, FailureType.TIMEOUT): "Global Timeout Hint",
            ("S1", None): "Stage S1 Hint"
        }
    )

    # 1. Test Global Failure Fallback
    @challenge(my_chall)
    def timeout_func(n):
        time.sleep(0.1)
        return n
    
    result = run_benchmarks(timeout=0.01, print_results=False, max_executions=1, warmup_executions=0)
    assert any(h['message'] == "Global Timeout Hint" for h in result.hints)
    
    clear_registry()
    reset()
    
    # 2. Test Stage-Level Fallback
    @challenge(my_chall)
    def crash_func(n):
        raise ValueError("Crash")
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    # FailureType.EXCEPTION is not in hints, so should fallback to ("S1", None)
    assert any(h['message'] == "Stage S1 Hint" for h in result.hints)

def test_staged_feedback_timeout():
    def slow_ref(n):
        time.sleep(0.01) # Reference takes 0.01s
        return n
        
    my_chall = Challenge(
        name="Fast Challenge",
        parameters=["n"],
        stages={
            "Basic": {"Small": (1,)},
            "Scale": {"Large": (100,)}
        },
        reference=slow_ref,
        timeout_multiplier=0.5, # student must be < 0.005s (impossible if they sleep 0.02)
        hints={
            ("Scale", FailureType.TIMEOUT): "Your solution is too slow for large inputs."
        }
    )
    
    @challenge(my_chall)
    def student_solution(n):
        # Scale stage should timeout
        if n > 10:
            time.sleep(0.05)
        return n
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    assert any(h['message'] == "Your solution is too slow for large inputs." for h in result.hints)
