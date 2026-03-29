import pytest
import random
from benchmark_my_code import challenge, Challenge, ForbiddenCallError, clear_registry, run_benchmarks

def setup_function():
    clear_registry()

def test_challenge_banned_calls():
    # A challenge that forbids 'sorted'
    my_chall = Challenge(
        name="No Shortcuts",
        parameters=["data"],
        variants=[([1, 2],)],
        banned_calls=["sorted"]
    )
    
    with pytest.raises(ForbiddenCallError) as excinfo:
        @challenge(my_chall)
        def my_sort(data):
            return sorted(data) # Forbidden!
            
    assert "Challenge forbids the use of: sorted" in str(excinfo.value)

def test_challenge_variant_generator():
    def my_gen():
        return [([1, 2, 3],), ([4, 5, 6],)]
        
    my_chall = Challenge(
        name="Gen Challenge",
        parameters=["data"],
        variants=my_gen
    )
    
    @challenge(my_chall)
    def my_sum(data):
        return sum(data)
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    # Check if both variants from generator were run
    func = result.get_function('my_sum')
    assert func.variant_count == 2

def test_challenge_reference_inclusion():
    my_chall = Challenge(
        name="Ref Challenge",
        parameters=["x"],
        variants=[(1,), (2,)],
        reference=lambda x: x * 2
    )
    
    @challenge(my_chall)
    def student_func(x):
        return x * 2
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    
    # Should find the reference function in results
    # The reference function name is automatically generated if it's a lambda
    ref_funcs = [f for f in result.functions if "Reference" in f.name]
    assert len(ref_funcs) == 1
    assert result.get_function('student_func') is not None

def test_challenge_validation_against_reference():
    my_chall = Challenge(
        name="Valid Ref",
        parameters=["x"],
        variants=[(5,)],
        reference=lambda x: 10
    )
    
    @challenge(my_chall)
    def broken_student(x):
        return 0 # WRONG! Should be 10
        
    from benchmark_my_code import InconsistentOutcomesError
    with pytest.raises(InconsistentOutcomesError):
        run_benchmarks(validate=True, max_executions=1)
