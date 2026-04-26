from benchmark_my_code import benchit
import time

@benchit
def fast_func():
    time.sleep(0.001)
    return True

@benchit
def slow_func():
    time.sleep(0.005)
    return True
