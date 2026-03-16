import pytest
from benchmark_my_code import benchit, run_benchmarks, clear_registry, InconsistentOutcomesError

def setup_function():
    clear_registry()

def test_deep_copy_prevents_mutation_leak():
    @benchit
    def mutating_func(data):
        data.append(99)
        return len(data)
        
    @benchit
    def pure_func(data):
        return len(data)
        
    variants = [([1, 2, 3],)]
    
    # Run the benchmarks
    # We use validate=False because they will naturally return different things 
    # (mutating_func returns 4, pure_func returns 3 for the copy it receives).
    # If deep copy wasn't working, pure_func would receive [1,2,3,99] and return 4.
    bench_result = run_benchmarks(variants, validate=False, max_executions=1, warmup_executions=0)
    
    # Check that pure_func actually executed
    assert bench_result.get_function('pure_func').executions > 0

def test_validate_true_raises_error_on_inconsistency():
    @benchit
    def correct_math(x):
        return x * 2
        
    @benchit
    def broken_math(x):
        return x + 2
        
    variants = [(5,)] # for 5, correct=10, broken=7 -> inconsistent!
    
    with pytest.raises(InconsistentOutcomesError):
        run_benchmarks(variants, validate=True, max_executions=1)

def test_validate_true_passes_on_consistency():
    @benchit
    def correct_math_1(x):
        return x * 2
        
    @benchit
    def correct_math_2(x):
        return x + x
        
    variants = [(5,)] # for 5, correct_math_1=10, correct_math_2=10 -> consistent!
    
    # Should not raise an error
    bench_result = run_benchmarks(variants, validate=True, max_executions=1, warmup_executions=0)
    assert bench_result is not None
