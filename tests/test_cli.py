import subprocess
import sys
import os

def test_cli_discovery():
    # Use uv run benchit to ensure it uses the current environment
    cmd = ["uv", "run", "benchit", "tests/cli_test_case.py", "--max-executions", "5", "--warmup-executions", "0"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "fast_func" in result.stdout
    assert "slow_func" in result.stdout
    # Check for the results table header or parts of it
    assert "Median (s)" in result.stdout

def test_cli_file_not_found():
    cmd = ["uv", "run", "benchit", "non_existent_file.py"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "Error: Path 'non_existent_file.py' not found." in result.stdout
