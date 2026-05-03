import pytest
import time
from benchmark_my_code.orchestrator import run_challenge
from benchmark_my_code.model import Challenge, Benchmark, FailureType

def test_malformed_reference_fails_gracefully():
    # A reference that crashes
    def ref(x): raise ValueError("Ref Crash")
    chall = Challenge("Crash Test", ["x"], variants=[(1,)], reference=ref)
    
    def student(x): return x
    
    benchmark = Benchmark()
    run_challenge(chall, [student], benchmark, print_results=False)
    
    # Student should be marked with BASELINE_FAILURE
    f_student = benchmark.get_function("student")
    # variant label for (1,) is '1'
    assert f_student.get_status('1') == FailureType.BASELINE_FAILURE

def test_extremely_fast_reference_honors_floor():
    # A reference that is nearly instantaneous
    def ref(x): return x
    # Multiplier 0.1 of 0s would be 0s, but floor is 1ms
    chall = Challenge("Fast Test", ["x"], variants=[(1,)], reference=ref, timeout_multiplier=0.1)
    
    # Student takes 0.005s (5ms)
    def student(x):
        time.sleep(0.005)
        return x
    
    benchmark = Benchmark()
    run_challenge(chall, [student], benchmark, print_results=False, max_executions=1, warmup_executions=0)
    
    f_student = benchmark.get_function("student")
    # 5ms > 1ms floor -> Timeout
    assert f_student.get_status('1') == FailureType.TIMEOUT

def test_multiplier_less_than_one_enforcement():
    # Reference takes 0.02s
    def ref(x):
        time.sleep(0.02)
        return x
    
    # Student has 0.5x multiplier -> 0.01s timeout
    chall = Challenge("Strict Test", ["x"], variants=[(1,)], reference=ref, timeout_multiplier=0.5)
    
    # Student takes 0.015s
    def student(x):
        time.sleep(0.015)
        return x
        
    benchmark = Benchmark()
    run_challenge(chall, [student], benchmark, print_results=False, max_executions=1, warmup_executions=0)
    
    f_student = benchmark.get_function("student")
    assert f_student.get_status('1') == FailureType.TIMEOUT

def test_correctness_by_default_from_reference():
    # No 'expected' provided in variants
    def ref(x): return x * 2
    chall = Challenge("Correctness Test", ["x"], variants=[(10,)], reference=ref)
    
    # Student returns wrong value
    def student(x): return x + 1 # 20 != 11 for x=10
    
    benchmark = Benchmark()
    run_challenge(chall, [student], benchmark, print_results=False, max_executions=1, warmup_executions=0)
    
    f_student = benchmark.get_function("student")
    assert f_student.get_status('10') == FailureType.CORRECTNESS

def test_keyword_argument_preservation():
    # Challenge using kwargs in variants
    def ref(a, b=0): return a + b
    variants = {"v1": {"args": (1,), "kwargs": {"b": 2}}}
    chall = Challenge("Kwargs Test", ["a", "b"], variants=variants, reference=ref)
    
    def student(a, b=0): return a + b
    
    benchmark = Benchmark()
    run_challenge(chall, [student], benchmark, print_results=False, max_executions=1, warmup_executions=0)
    
    f_student = benchmark.get_function("student")
    # Result should be 3 (1+2), so status should be NONE (success)
    assert f_student.get_status('v1') == FailureType.NONE
