import pytest
import time
from benchmark_my_code import challenge, run_benchmarks, FailureType, clear_registry

def setup_function():
    clear_registry()

def test_pedagogical_hints_timeout():
    stages = {
        "Small": [([1, 2], [1, 2])],
        "Large": [([i for i in range(100)], [i for i in range(100)])]
    }
    
    hints = {
        ("Large", FailureType.TIMEOUT): "Consider a more efficient algorithm for large data."
    }
    
    # We use a very low timeout via multiplier or absolute timeout if we could
    # run_benchmarks passes kwargs to run_challenge, which passes them to bench.
    # bench has a 'timeout' param.
    
    @challenge(stages=stages, hints=hints, timeout_multiplier=0.1)
    def student_func(data):
        if len(data) > 50:
            time.sleep(0.5) # Should timeout if ref is fast
        return data

    def reference_func(data):
        return data

    # Update challenge to include reference
    clear_registry()
    @challenge(stages=stages, hints=hints, reference=reference_func, timeout_multiplier=0.1)
    def student_func_fixed(data):
        if len(data) > 50:
            time.sleep(0.5)
        return data

    result = run_benchmarks(print_results=True, max_executions=1, warmup_executions=0)
    
    assert any(h['message'] == "Consider a more efficient algorithm for large data." for h in result.hints)
    assert any(h['stage'] == "Large" for h in result.hints)

def test_pedagogical_hints_template():
    stages = {
        "Correctness": [([1, 2], [1, 2])]
    }
    
    hints = {
        ("Correctness", FailureType.CORRECTNESS): "Expected {expected} but got {actual} for variant {variant}."
    }
    
    @challenge(stages=stages, hints=hints)
    def student_func(data):
        return [1] # Wrong
        
    result = run_benchmarks(print_results=True, max_executions=1, warmup_executions=0)
    
    assert any("Expected [1, 2] but got [1]" in h['message'] for h in result.hints)

def test_pedagogical_hints_named_variant():
    stages = {
        "Edge": {"Empty List": ([], [1])} # Intentionally wrong expected for test
    }
    
    hints = {
        ("Empty List", FailureType.CORRECTNESS): "Specific hint for Empty List variant."
    }
    
    @challenge(stages=stages, hints=hints)
    def student_func(data):
        return data
        
    result = run_benchmarks(print_results=True, max_executions=1, warmup_executions=0)
    
    assert any("Specific hint for Empty List variant." in h['message'] for h in result.hints)
