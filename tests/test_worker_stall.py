import pytest
import time
import threading
from benchmark_my_code.orchestrator import BenchmarkingWorker, bench

# A "controlled" infinite loop for testing
STOP_EVENT = threading.Event()

def infinite_loop():
    while not STOP_EVENT.is_set():
        time.sleep(0.01)

@pytest.fixture(autouse=True)
def manage_stop_event():
    global STOP_EVENT
    STOP_EVENT.clear()
    yield
    STOP_EVENT.set()
    time.sleep(0.1)

def test_worker_stall_on_timeout():
    worker = BenchmarkingWorker()
    
    with pytest.raises(TimeoutError):
        # Very short timeout to trigger it quickly
        worker.run(infinite_loop, timeout=0.05)
    
    assert worker._stalled is True
    
    with pytest.raises(RuntimeError) as excinfo:
        worker.run(lambda: "success")
    
    assert "STALLED" in str(excinfo.value)

def test_bench_handles_stall():
    # bench() catches TimeoutError internally to update function status
    bench(infinite_loop, max_executions=1, timeout=0.05, warmup_executions=0)
    
    assert BenchmarkingWorker()._stalled is True
    
    # Subsequent bench calls should fail immediately with RuntimeError
    with pytest.raises(RuntimeError):
        bench(lambda: 1)

def test_worker_singleton():
    w1 = BenchmarkingWorker()
    w2 = BenchmarkingWorker()
    assert w1 is w2
