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
    worker.reset() # Ensure clean state
    
    with pytest.raises(TimeoutError):
        # Very short timeout to trigger it quickly
        worker.run(infinite_loop, timeout=0.05)
    
    assert worker._stalled is True
    
    with pytest.raises(RuntimeError) as excinfo:
        worker.run(lambda: "success")
    
    assert "TERMINATED" in str(excinfo.value)
    assert "reset()" in str(excinfo.value)

def test_worker_recovery_via_reset():
    worker = BenchmarkingWorker()
    worker.reset()
    
    with pytest.raises(TimeoutError):
        worker.run(infinite_loop, timeout=0.05)
    
    assert worker._stalled is True
    
    # Recover
    worker.reset()
    assert worker._stalled is False
    assert worker._orphan_count >= 1 # The infinite loop thread is now an orphan
    
    # Should work now
    result, _ = worker.run(lambda: "recovered")
    assert result == "recovered"

def test_orphan_threshold():
    from benchmark_my_code.orchestrator import reset
    worker = BenchmarkingWorker()
    worker.reset()
    worker._orphan_count = 0 # Force reset for test
    
    # Simulate reaching threshold
    worker._orphan_count = worker.ORPHAN_THRESHOLD
    worker._stalled = True
    
    with pytest.raises(RuntimeError) as excinfo:
        worker.run(lambda: 1)
    
    assert "consuming resources" in str(excinfo.value)
    assert "restart is now required" in str(excinfo.value)
    
    # Cleanup for other tests
    worker._orphan_count = 0
    worker.reset()

def test_bench_handles_stall():
    from benchmark_my_code.orchestrator import reset
    reset()
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
