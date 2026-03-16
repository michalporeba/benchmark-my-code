import benchmark_my_code as bmc
import logging


logging.basicConfig(level=logging.DEBUG)


def collatz(n):
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps


bmc.bench(collatz, range(1, 5), max_executions=100)
