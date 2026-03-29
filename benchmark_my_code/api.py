from typing import Any, Callable, List, Union, Iterable
from .orchestrator import bench, measure_time, normalised_variants
from .model import Challenge, Benchmark
import logging
import inspect
import ast
import copy
import random

_GLOBAL_REGISTRY: List[Callable] = []
_CHALLENGE_REGISTRY: List[tuple[Callable, Challenge]] = []

class InconsistentOutcomesError(Exception):
    pass

class InvalidSignatureError(Exception):
    pass

class ForbiddenCallError(Exception):
    pass

def benchit(func: Callable) -> Callable:
    """Decorator to register a function for ad-hoc benchmarking."""
    _GLOBAL_REGISTRY.append(func)
    return func

def validate_signature(func: Callable, expected_params: List[str]):
    """Validates that a function signature matches the expected parameters."""
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    if params != expected_params:
        stub = f"def {func.__name__}({', '.join(expected_params)}):"
        raise InvalidSignatureError(
            f"Function '{func.__name__}' has an invalid signature.\n"
            f"Expected: {stub}\n"
            f"Found:    def {func.__name__}({', '.join(params)}):"
        )

class ForbiddenCallVisitor(ast.NodeVisitor):
    def __init__(self, banned_list):
        self.banned_list = banned_list
        self.found = []

    def visit_Call(self, node):
        # Handle simple calls: func()
        if isinstance(node.func, ast.Name):
            if node.func.id in self.banned_list:
                self.found.append(node.func.id)
        # Handle attribute calls: obj.method()
        elif isinstance(node.func, ast.Attribute):
            full_name = f"{node.func.attr}" # For simplicity, just check method name
            if full_name in self.banned_list:
                self.found.append(full_name)
        self.generic_visit(node)

import textwrap

def validate_algorithmic_constraints(func: Callable, banned_calls: List[str]):
    """Checks if the function uses any forbidden built-ins or methods."""
    if not banned_calls:
        return

    try:
        source = textwrap.dedent(inspect.getsource(func))
        tree = ast.parse(source)
        visitor = ForbiddenCallVisitor(banned_calls)
        visitor.visit(tree)
        
        if visitor.found:
            forbidden = ", ".join(set(visitor.found))
            raise ForbiddenCallError(
                f"Challenge forbids the use of: {forbidden}.\n"
                f"Function '{func.__name__}' must be implemented from scratch."
            )
    except (OSError, TypeError):
        # Fallback if source cannot be retrieved (e.g. REPL)
        logging.warning(f"Could not retrieve source for '{func.__name__}'. Algorithmic constraints not verified.")

def challenge(challenge_obj: Challenge):
    """Decorator to register a function for a specific challenge."""
    def decorator(func: Callable) -> Callable:
        validate_signature(func, challenge_obj.parameters)
        validate_algorithmic_constraints(func, challenge_obj.banned_calls)
        _CHALLENGE_REGISTRY.append((func, challenge_obj))
        return func
    return decorator

def run_benchmarks(variants: Any = None, validate: bool = False, print_results: bool = True, **kwargs):
    """
    Runs benchmarks for all registered functions.
    If validate=True, ensures all functions return the same result for each variant.
    """
    if not _GLOBAL_REGISTRY and not _CHALLENGE_REGISTRY:
        logging.warning("No functions registered for benchmarking. Use @benchit or @challenge decorators.")
        return None

    total_benchmark = Benchmark()

    # 1. Run Ad-hoc benchmarks
    if _GLOBAL_REGISTRY:
        if validate:
            for (args, kwargs_variant, name) in normalised_variants(variants):
                results = {}
                for func in _GLOBAL_REGISTRY:
                    safe_args = copy.deepcopy(args)
                    safe_kwargs = copy.deepcopy(kwargs_variant)
                    try:
                        result, _ = measure_time(func, safe_args, safe_kwargs)
                        results[func.__name__] = result
                    except Exception as e:
                        results[func.__name__] = f"<Exception: {e}>"

                unique_results = list(results.values())
                if not all(res == unique_results[0] for res in unique_results):
                    variant_label = name or f"args={args}, kwargs={kwargs_variant}"
                    error_msg = f"Inconsistent outcomes for variant ({variant_label}):\n"
                    for name, res in results.items():
                        error_msg += f"  {name} -> {res}\n"
                    raise InconsistentOutcomesError(error_msg)

        adhoc_bench = bench(_GLOBAL_REGISTRY, variants=variants, **kwargs)
        for f in adhoc_bench.functions:
            total_benchmark.add_function(f)

    # 2. Run Challenge benchmarks
    # Group by challenge to ensure variant generator runs once per challenge
    by_challenge = {}
    for func, chall in _CHALLENGE_REGISTRY:
        if chall not in by_challenge:
            by_challenge[chall] = []
        by_challenge[chall].append(func)

    for chall, funcs in by_challenge.items():
        # Handle variant generator
        actual_variants = chall.variants
        if callable(actual_variants):
            random.seed(42) # Ensure predictable randomness for pedagogical fairness
            actual_variants = actual_variants()

        # Include reference implementation if it exists
        all_to_run = list(funcs)
        if chall.reference:
            # We wrap the reference to label it clearly
            ref_func = chall.reference
            if not hasattr(ref_func, '__name__') or ref_func.__name__ == '<lambda>':
                ref_func.__name__ = f"Reference_{chall.name.replace(' ', '_')}"
            all_to_run.insert(0, ref_func)

        # Validation against reference
        if validate and chall.reference:
            for (args, kwargs_variant, name) in normalised_variants(actual_variants):
                variant_label = name or f"args={args}"
                ref_res, _ = measure_time(chall.reference, copy.deepcopy(args), copy.deepcopy(kwargs_variant))
                for func in funcs:
                    student_res, _ = measure_time(func, copy.deepcopy(args), copy.deepcopy(kwargs_variant))
                    if student_res != ref_res:
                        raise InconsistentOutcomesError(
                            f"Student solution '{func.__name__}' failed correctness check against reference.\n"
                            f"Variant:  {variant_label}\n"
                            f"Expected: {ref_res}\n"
                            f"Got:      {student_res}"
                        )

        chall_bench = bench(all_to_run, variants=actual_variants, **kwargs)
        for f in chall_bench.functions:
            total_benchmark.add_function(f)

    from .result import BenchmarkResult
    result = BenchmarkResult(total_benchmark)
    
    if print_results:
        print(result)
        
    return result

def clear_registry():
    _GLOBAL_REGISTRY.clear()
    _CHALLENGE_REGISTRY.clear()
