import pytest
from benchmark_my_code import challenge, Challenge, InvalidSignatureError, clear_registry, run_benchmarks

def setup_function():
    clear_registry()

def test_challenge_signature_validation_success():
    sort_challenge = Challenge(
        name="Sort",
        parameters=["data"],
        variants=[([1, 2],)]
    )
    
    @challenge(sort_challenge)
    def my_sort(data):
        return sorted(data)
    
    # Should not raise error

def test_challenge_signature_validation_failure_wrong_count():
    sort_challenge = Challenge(
        name="Sort",
        parameters=["data"],
        variants=[([1, 2],)]
    )
    
    with pytest.raises(InvalidSignatureError) as excinfo:
        @challenge(sort_challenge)
        def my_sort(data, extra):
            return data
            
    assert "Expected: def my_sort(data):" in str(excinfo.value)
    assert "Found:    def my_sort(data, extra):" in str(excinfo.value)

def test_challenge_signature_validation_failure_wrong_names():
    sort_challenge = Challenge(
        name="Sort",
        parameters=["data"],
        variants=[([1, 2],)]
    )
    
    with pytest.raises(InvalidSignatureError) as excinfo:
        @challenge(sort_challenge)
        def my_sort(items):
            return items
            
    assert "Expected: def my_sort(data):" in str(excinfo.value)

def test_run_benchmarks_with_challenge():
    sort_challenge = Challenge(
        name="Sort",
        parameters=["data"],
        variants=[([3, 1, 2],)]
    )
    
    @challenge(sort_challenge)
    def my_sort(data):
        return sorted(data)
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    assert result.get_function('my_sort') is not None
    # Note: currently it runs 1 batch of 1 execution if max_executions=1
    assert result.get_function('my_sort').executions == 1
