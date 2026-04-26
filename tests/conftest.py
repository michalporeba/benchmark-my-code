import pytest
from benchmark_my_code.orchestrator import BenchmarkingWorker

@pytest.fixture(autouse=True)
def reset_worker_fixture():
    # Reset before each test to ensure a clean state
    BenchmarkingWorker()._reset()
    yield
    # Reset after each test to clean up any leftover stall
    BenchmarkingWorker()._reset()
