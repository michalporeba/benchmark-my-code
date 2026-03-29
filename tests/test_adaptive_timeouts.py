import pytest
import time
from benchmark_my_code import challenge, Challenge, run_benchmarks, clear_registry

def setup_function():
    clear_registry()

def test_adaptive_timeout_fairness():
    # 1. Educator provides a reference that takes ~0.01s
    def professor_ref(x):
        time.sleep(0.01)
        return x
        
    my_chall = Challenge(
        name="Sleep Challenge",
        parameters=["x"],
        variants=[(1,)],
        reference=professor_ref,
        timeout_multiplier=2.0 # student has 0.02s
    )
    
    # 2. Student writes a solution that takes ~0.05s (should time out)
    @challenge(my_chall)
    def slow_student(x):
        time.sleep(0.05)
        return x
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    
    # The student function should be in the result, but with 0 executions 
    # (or marked as timeout if we had a specific status, currently it just breaks the loop)
    # Actually, in orchestrator.py, if a TimeoutError occurs, it records a timeout and breaks the loop.
    # total_executions for that variant will be 0 if the first execution timed out.
    
    func = result.get_function('slow_student')
    # Because it timed out on every run of the first batch, it should have 0 successful executions
    assert func.executions == 0

def test_adaptive_timeout_passes_when_efficient():
    def professor_ref(x):
        time.sleep(0.02)
        return x
        
    my_chall = Challenge(
        name="Efficiency Challenge",
        parameters=["x"],
        variants=[(1,)],
        reference=professor_ref,
        timeout_multiplier=2.0 # student has 0.04s
    )
    
    @challenge(my_chall)
    def fast_student(x):
        time.sleep(0.01) # efficient!
        return x
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    func = result.get_function('fast_student')
    assert func.executions > 0
