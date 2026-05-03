import statistics
import array
from typing import Any
from enum import Enum, auto

class FailureType(Enum):
    NONE = auto()
    PENDING = auto()
    CORRECTNESS = auto()
    TIMEOUT = auto()
    EXCEPTION = auto()
    CONSTRAINT = auto()


class Function:
    def __init__(self, function: callable):
        self._name = function.__name__
        self._function = function
        self._executions = {} 
        self._total_time = {}
        self._max_time = {}
        self._min_time = {}
        self._status = {} # Map variant -> FailureType
        self._peak_memory = {} # Map variant -> float (bytes)

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)

    @property
    def name(self):
        return self._name

    @property
    def executions(self):
        return sum(len(exs) for exs in self._executions.values())

    @property
    def variant_count(self):
        return len(self._executions)

    def total_time(self, variant=None):
        if variant:
            return self._total_time.get(variant, 0)
        return sum(self._total_time.values())

    def min_time(self, variant=None):
        if variant:
            return self._min_time.get(variant, 0)
        return min(self._min_time.values()) if self._min_time else 0
    
    def max_time(self, variant=None):
        if variant:
            return self._max_time.get(variant, 0)
        return max(self._max_time.values()) if self._max_time else 0

    def median_time(self, variant=None):
        if variant:
            executions = self._executions.get(variant, None)
            if not executions:
                return 0
            return self._calculate_median(executions)
        
        # If no variant specified, get median across all executions of all variants
        # Use array.array to avoid massive temporary list creation
        all_executions = array.array('d')
        for exs in self._executions.values():
            all_executions.extend(exs)
        
        if not all_executions:
            return 0
        return self._calculate_median(all_executions)

    def _calculate_median(self, data: array.array) -> float:
        n = len(data)
        if n == 0:
            return 0.0
        
        # We must copy because Quickselect is in-place, and we don't want to 
        # mutate the original execution history. We use array.array for the copy
        # to remain memory-efficient (avoiding Python float object overhead).
        work_arr = array.array('d', data)
        
        mid = n // 2
        if n % 2 == 1:
            return self._quickselect(work_arr, mid)
        else:
            # For even length, we need the average of mid-1 and mid.
            # After finding mid, elements at [0...mid-1] are all <= work_arr[mid].
            # The value at mid-1 is the maximum of the elements in that range.
            v2 = self._quickselect(work_arr, mid)
            v1 = work_arr[0]
            for i in range(1, mid):
                if work_arr[i] > v1:
                    v1 = work_arr[i]
            return (v1 + v2) / 2.0

    def _quickselect(self, arr: array.array, k: int) -> float:
        """Iterative Quickselect implementation to find the k-th smallest element."""
        left = 0
        right = len(arr) - 1
        while left <= right:
            if left == right:
                return arr[left]
            
            # Simple pivot selection: middle element
            pivot_index = (left + right) // 2
            pivot_val = arr[pivot_index]
            
            # Partition
            arr[pivot_index], arr[right] = arr[right], arr[pivot_index]
            store_index = left
            for i in range(left, right):
                if arr[i] < pivot_val:
                    arr[store_index], arr[i] = arr[i], arr[store_index]
                    store_index += 1
            arr[right], arr[store_index] = arr[store_index], arr[right]
            
            if k == store_index:
                return arr[k]
            elif k < store_index:
                right = store_index - 1
            else:
                left = store_index + 1
        return 0.0

    def record_execution_time(self, variant: str, time: float) -> None:
        if variant not in self._executions:
            self._executions[variant] = array.array('d')
            self._total_time[variant] = 0
            self._min_time[variant] = time
            self._max_time[variant] = time
            self._status[variant] = FailureType.NONE
            self._peak_memory[variant] = 0.0

        self._executions[variant].append(time)        
        self._total_time[variant] += time 
        self._min_time[variant] = min(self._min_time[variant], time)
        self._max_time[variant] = max(self._max_time[variant], time)

    def merge(self, other: 'Function') -> None:
        """Merges execution data from another Function object into this one."""
        for variant, times in other._executions.items():
            if variant not in self._executions:
                self._executions[variant] = array.array('d')
                self._total_time[variant] = 0
                self._min_time[variant] = other._min_time[variant]
                self._max_time[variant] = other._max_time[variant]
                self._status[variant] = other._status.get(variant, FailureType.NONE)
                self._peak_memory[variant] = other._peak_memory.get(variant, 0.0)
            
            self._executions[variant].extend(times)
            self._total_time[variant] += other._total_time[variant]
            self._min_time[variant] = min(self._min_time[variant], other._min_time[variant])
            self._max_time[variant] = max(self._max_time[variant], other._max_time[variant])
            self._peak_memory[variant] = max(self._peak_memory[variant], other._peak_memory.get(variant, 0.0))

    def record_status(self, variant: str, status: FailureType) -> None:
        self._status[variant] = status

    def get_status(self, variant: str) -> FailureType:
        return self._status.get(variant, FailureType.NONE)

    def record_memory(self, variant: str, peak_bytes: float) -> None:
        self._peak_memory[variant] = peak_bytes

    def get_memory(self, variant: str) -> float:
        return self._peak_memory.get(variant, 0.0)

    def check_convergence(self, variant: str, previous_median: float) -> tuple[bool, float]:
        """
        Evaluates if the current median has converged relative to a previous median.
        Returns a tuple: (has_converged: bool, current_median: float)
        """
        current_median = self.median_time(variant)
        
        if previous_median == 0 and current_median == 0:
            return True, current_median
        elif previous_median == 0:
            return False, current_median
            
        change_rate = abs((current_median - previous_median) / previous_median)
        return change_rate < 0.01, current_median

    def get_executions(self, variant: str):
        return self._executions.get(variant, [])

    def record_timeout(self, variant: str) -> None:
        self._status[variant] = FailureType.TIMEOUT

    def record_exception(self, variant: str, exception: Exception) -> None: 
        self._status[variant] = FailureType.EXCEPTION


class Challenge:
    """Defines a benchmarking challenge with a specific contract."""
    def __init__(self, name: str, parameters: list[str], variants: Any = None, reference: callable = None, banned_calls: list[str] = None, timeout_multiplier: float = 10.0, stages: dict = None, hints: dict = None):
        self.name = name
        self.parameters = parameters
        self.variants = variants
        self.reference = reference
        self.banned_calls = banned_calls or []
        self.timeout_multiplier = timeout_multiplier
        self.stages = stages or {}
        self.hints = hints or {}


class Benchmark:
    def __init__(self):
        self._functions = {} 

    def add_function(self, function: Function) -> 'Benchmark':
        if function.name in self._functions:
            self._functions[function.name].merge(function)
        else:
            self._functions[function.name] = function
        return self

    @property
    def functions(self):
        return self._functions.values()

    def get_function(self, name: str) -> Function:
        return self._functions.get(name, None)
