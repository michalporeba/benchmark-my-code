from typing import Any, Callable, List
from .orchestrator import bench
import logging

_GLOBAL_REGISTRY: List[Callable] = []

class InconsistentOutcomesError(Exception):
    pass

def benchit(func: Callable) -> Callable:
    """Decorator to register a function for ad-hoc benchmarking."""
    _GLOBAL_REGISTRY.append(func)
    return func

def run_benchmarks(variants: Any = None, validate: bool = False, **kwargs):
    """
    Runs benchmarks for all registered functions.
    If validate=True, ensures all functions return the same result for each variant.
    """
    if not _GLOBAL_REGISTRY:
        logging.warning("No functions registered for benchmarking. Use @benchit decorator.")
        return None

    # Optional: We can validate consistency before doing the heavy benchmarking
    if validate:
        from .orchestrator import normalised_variants, measure_time
        import copy
        
        for (args, kwargs_variant, _) in normalised_variants(variants):
            results = {}
            for func in _GLOBAL_REGISTRY:
                # Deep copy to ensure no side effects
                safe_args = copy.deepcopy(args)
                safe_kwargs = copy.deepcopy(kwargs_variant)
                try:
                    result, _ = measure_time(func, safe_args, safe_kwargs)
                    results[func.__name__] = result
                except Exception as e:
                    results[func.__name__] = f"<Exception: {e}>"

            # Check if all results are identical
            unique_results = list(results.values())
            if not all(res == unique_results[0] for res in unique_results):
                error_msg = f"Inconsistent outcomes for variant (args={args}, kwargs={kwargs_variant}):\n"
                for name, res in results.items():
                    error_msg += f"  {name} -> {res}\n"
                raise InconsistentOutcomesError(error_msg)

    # Run the actual benchmarks
    return bench(_GLOBAL_REGISTRY, variants=variants, **kwargs)

# Allow clearing registry if needed
def clear_registry():
    _GLOBAL_REGISTRY.clear()
