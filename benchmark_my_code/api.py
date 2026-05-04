import logging
import copy
import sys
import os
import inspect
from typing import Any, Callable, List, Optional
from itertools import islice

from .orchestrator import bench, normalised_variants, format_parameters, BenchmarkingWorker, run_challenge, results_equal, VARIANT_LIMIT
from .model import Benchmark, Function, Challenge, FailureType
from .config import validate_algorithmic_constraints, validate_signature
from .exceptions import InconsistentOutcomesError, InvalidSignatureError, ForbiddenCallError

_GLOBAL_REGISTRY = []
_CHALLENGE_REGISTRY = []
_DISCOVERY_CACHE = {}

def clear_registry():
    """Clears all registered benchmarks and challenges."""
    global _GLOBAL_REGISTRY, _CHALLENGE_REGISTRY, _DISCOVERY_CACHE
    _GLOBAL_REGISTRY = []
    _CHALLENGE_REGISTRY = []
    _DISCOVERY_CACHE = {}

def benchit(arg: Any = None, **kwargs):
    """
    Decorator for simple benchmarks.
    """
    ensure_copy = kwargs.get('ensure_copy', True)
    variants = kwargs.get('variants')
    is_reference = kwargs.get('is_reference', False)

    if arg is not None:
        if isinstance(arg, bool):
            ensure_copy = arg
        elif callable(arg) and not kwargs and variants is None:
            func = arg
            _GLOBAL_REGISTRY.append(func)
            setattr(func, "_bmc_ensure_copy", True)
            return func
        else:
            variants = arg

    def decorator(func):
        _GLOBAL_REGISTRY.append(func)
        if variants is not None:
            setattr(func, "_bench_variants", variants)
        
        setattr(func, "_bmc_ensure_copy", ensure_copy)
        setattr(func, "_bmc_is_reference", is_reference)
            
        if kwargs:
            setattr(func, "_bench_options", kwargs)
        return func
    
    return decorator

def challenge(name_or_challenge: Any = None, variants: Any = None, reference: callable = None, banned_calls: List[str] = None, timeout_multiplier: float = 10.0, stages: dict = None, hints: dict = None, **kwargs):
    """
    Decorator for challenge mode.
    """
    def decorator(func):
        sig = inspect.signature(func)
        func_params = list(sig.parameters.keys())

        if isinstance(name_or_challenge, Challenge):
            challenge_obj = name_or_challenge
            if not challenge_obj.name or challenge_obj.name == func.__name__:
                challenge_obj.name = func.__name__
            if not challenge_obj.parameters:
                challenge_obj.parameters = func_params
        else:
            name = name_or_challenge or func.__name__
            challenge_obj = Challenge(
                name=name,
                parameters=func_params,
                variants=variants,
                reference=reference,
                banned_calls=banned_calls,
                timeout_multiplier=timeout_multiplier,
                stages=stages,
                hints=hints
            )
        
        if kwargs:
            setattr(func, "_bench_options", kwargs)
        setattr(func, "_bmc_ensure_copy", kwargs.get('ensure_copy', True))

        validate_signature(func, challenge_obj.parameters)
        validate_algorithmic_constraints(func, challenge_obj.banned_calls)
        _CHALLENGE_REGISTRY.append((func, challenge_obj))
        return func
    return decorator

def find_user_frame():
    """
    Walks back the stack to find the first frame that is not in the benchmark_my_code package.
    """
    package_dir = os.path.dirname(os.path.abspath(__file__))
    
    frame = sys._getframe(1)
    while frame:
        filename = frame.f_code.co_filename
        # Improved pseudo-file detection
        is_pseudo = (filename.startswith('<') and filename.endswith('>')) or \
                    'pytest' in filename.lower()
        
        is_ipython = filename.startswith('<ipython-input-')
        
        if (is_pseudo or is_ipython) and not filename.startswith('<decorator-gen-'):
            # If it's a pseudo-file, it's likely user code (Jupyter/Notebook/CLI wrapper)
            return frame
            
        frame_file = os.path.abspath(filename)
        if not frame_file.startswith(package_dir):
            return frame
        frame = frame.f_back
    return None

def _safe_deepcopy(obj):
    try:
        return copy.deepcopy(obj)
    except Exception:
        return obj

def _resolve_variants_for_func(func, provided_variants):
    if provided_variants is not None:
        return provided_variants
    
    explicit = getattr(func, "_bench_variants", None)
    if explicit is not None:
        return explicit
        
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    if not params:
        return None
        
    frame = find_user_frame()
    if not frame:
        return None
    
    # Finding 6: Support multi-param discovery and standard names
    candidate_names = params + ["scenarios", "data"]
    
    for param_name in candidate_names:
        # Revert to id(frame) for discovery during run_benchmarks
        cache_key = (id(frame), param_name)
        if cache_key in _DISCOVERY_CACHE:
            return _DISCOVERY_CACHE[cache_key]

        val = frame.f_locals.get(param_name)
        if val is None:
            val = frame.f_globals.get(param_name)
        
        if val is None:
            continue

        if callable(val) and not isinstance(val, type):
            try:
                p_sig = inspect.signature(val)
                if not p_sig.parameters:
                    val = val()
            except Exception:
                pass
        
        if hasattr(val, "__iter__") and not isinstance(val, (list, tuple, dict, str, set)):
            # Finding 7: Truncation warning
            val = list(islice(val, VARIANT_LIMIT + 1))
            if len(val) > VARIANT_LIMIT:
                logging.warning(f"Auto-discovery for '{param_name}' truncated to {VARIANT_LIMIT} items.")
                val = val[:VARIANT_LIMIT]
        
        _DISCOVERY_CACHE[cache_key] = val
        return val
            
    return None

def run_benchmarks(variants: Any = None, validate: bool = False, print_results: bool = True, **kwargs):
    global _DISCOVERY_CACHE
    _DISCOVERY_CACHE = {}

    if not _GLOBAL_REGISTRY and not _CHALLENGE_REGISTRY:
        logging.warning("No functions registered for benchmarking. Use @benchit or @challenge decorators.")
        return None

    total_benchmark = Benchmark()
    hints = []
    
    from .orchestrator import bench as bench_func
    bench_params = inspect.signature(bench_func).parameters
    valid_bench_keys = {p.name for p in bench_params.values()}
    global_bench_args = {k: v for k, v in kwargs.items() if k in valid_bench_keys}

    if _GLOBAL_REGISTRY:
        if print_results:
            print("\n🚀 Running Ad-hoc Benchmarks...")

        if validate:
            if print_results:
                print("  Validating outcomes across all registered functions...")
            
            common_variants = variants
            if common_variants is None and _GLOBAL_REGISTRY:
                common_variants = _resolve_variants_for_func(_GLOBAL_REGISTRY[0], None)
            
            if common_variants is not None:
                worker = BenchmarkingWorker()
                for (args, kwargs_variant, name, expected) in normalised_variants(common_variants):
                    results = {}
                    for func in _GLOBAL_REGISTRY:
                        f_ensure_copy = getattr(func, "_bmc_ensure_copy", True)
                        safe_args = _safe_deepcopy(args) if f_ensure_copy else args
                        safe_kwargs = _safe_deepcopy(kwargs_variant) if f_ensure_copy else kwargs_variant
                        try:
                            result, _ = worker.run(func, safe_args, safe_kwargs)
                            results[func.__name__] = result
                        except Exception as e:
                            results[func.__name__] = f"<Exception: {e}>"

                    # Finding 8: Use results_equal for robust validation
                    func_names = list(results.keys())
                    if len(func_names) > 1:
                        first_func = func_names[0]
                        first_res = results[first_func]
                        for other_func in func_names[1:]:
                            if not results_equal(first_res, results[other_func]):
                                variant_label = name or f"args={args}, kwargs={kwargs_variant}"
                                error_msg = f"Inconsistent outcomes for variant ({variant_label}):\n"
                                for f_name, res in results.items():
                                    error_msg += f"  {f_name} -> {res}\n"
                                raise InconsistentOutcomesError(error_msg)

        ref_func = next((f for f in _GLOBAL_REGISTRY if getattr(f, '_bmc_is_reference', False)), None)

        for func in _GLOBAL_REGISTRY:
            if print_results:
                ref_tag = " [Reference]" if getattr(func, '_bmc_is_reference', False) else ""
                print(f"  - Benchmarking '{func.__name__}'{ref_tag}...", end="", flush=True)

            func_variants = _resolve_variants_for_func(func, variants)
            f_options = getattr(func, "_bench_options", {})
            combined_bench_args = {**global_bench_args, **{k: v for k, v in f_options.items() if k in valid_bench_keys}}
            
            b = bench(func, variants=func_variants, **combined_bench_args)
            
            if print_results:
                print(" DONE")
            
            # Finding 5: Optimized reference comparison
            if ref_func and func != ref_func:
                ref_model = total_benchmark.get_function(ref_func.__name__)
                for f_model in b.functions:
                    for variant_label in list(f_model._status.keys()):
                        if f_model.get_status(variant_label) == FailureType.NONE:
                            # Try to get reference result from already executed benchmark
                            ref_res = None
                            if ref_model:
                                ref_res = ref_model.get_sample_result(variant_label)
                            
                            if ref_res is None:
                                # Fallback: re-run if not available
                                for (args, kwargs_v, label, _) in normalised_variants(func_variants):
                                    if label == variant_label:
                                        worker = BenchmarkingWorker()
                                        ref_res, _ = worker.run(ref_func, _safe_deepcopy(args), _safe_deepcopy(kwargs_v))
                                        break
                            
                            student_res = f_model.get_sample_result(variant_label)
                            if not results_equal(student_res, ref_res):
                                f_model.record_status(variant_label, FailureType.CORRECTNESS)

            for f in b.functions:
                total_benchmark.add_function(f)

    if _CHALLENGE_REGISTRY:
        if print_results:
            print("\n🏆 Running Challenges...")
        by_challenge = {}
        for func, chall in _CHALLENGE_REGISTRY:
            if chall not in by_challenge:
                by_challenge[chall] = []
            by_challenge[chall].append(func)
        for chall, funcs in by_challenge.items():
            hints.extend(run_challenge(chall, funcs, total_benchmark, **kwargs))

    from .result import BenchmarkResult
    result = BenchmarkResult(total_benchmark)
    result.hints = hints
    if print_results:
        print(result)
    return result
