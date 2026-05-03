import argparse
import importlib.util
import os
import sys
import ast
from typing import List
from .api import run_benchmarks, clear_registry

def has_benchmarks(file_path: str) -> bool:
    """Uses AST to check if a file contains @benchit or @challenge decorators."""
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    # Check for @benchit or @challenge
                    # Simple check for Name nodes. Could be more robust (Attribute nodes etc.)
                    if isinstance(decorator, ast.Name):
                        if decorator.id in ("benchit", "challenge"):
                            return True
                    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                        if decorator.func.id in ("benchit", "challenge"):
                            return True
                    elif isinstance(decorator, ast.Attribute) and decorator.attr in ("benchit", "challenge"):
                        return True
    except Exception:
        return False
    return False

def find_benchmarks(path: str) -> List[str]:
    """Recursively finds all .py files with benchmarks in a directory, or returns the file itself."""
    if os.path.isfile(path):
        return [path] if path.endswith(".py") and has_benchmarks(path) else []
    
    benchmarks = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    file_path = os.path.join(root, file)
                    if has_benchmarks(file_path):
                        benchmarks.append(file_path)
    return benchmarks

def load_benchmarks_safely(file_path: str):
    """
    Parses the file with AST, removes top-level script statements, 
    and executes the result to populate the registry without side effects.
    """
    with open(file_path, "r") as f:
        source = f.read()
    
    tree = ast.parse(source)
    
    # Filter top-level nodes: keep only imports, classes, and functions.
    # We also keep assignments to standard parametrization names like 'data', 'scenarios'.
    safe_nodes = []
    allowed_params = ["data", "scenarios"]
    
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            safe_nodes.append(node)
        elif isinstance(node, ast.Assign):
            # Keep if it assigns to one of the allowed parameter names
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in allowed_params:
                    safe_nodes.append(node)
                    break
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            # Keep if it's a call to @benchit or @challenge (though they are usually decorators)
            # This handles cases where people might use them as functions
            pass 

    tree.body = safe_nodes
    
    # Create a new module object
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    module = importlib.util.module_from_spec(
        importlib.util.spec_from_file_location(module_name, file_path)
    )
    
    # Add the file's directory to sys.path
    file_dir = os.path.dirname(os.path.abspath(file_path))
    if file_dir not in sys.path:
        sys.path.insert(0, file_dir)
        
    # Execute the transformed AST in the module's namespace
    code = compile(tree, filename=file_path, mode="exec")
    exec(code, module.__dict__)
    return module

def main():
    parser = argparse.ArgumentParser(prog="benchit", description="Benchmark My Code CLI runner.")
    parser.add_argument("path", help="The Python file or directory to benchmark.")
    # Add other arguments that run_benchmarks supports
    parser.add_argument("--max-executions", type=int, default=100)
    parser.add_argument("--warmup-executions", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=100.0)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' not found.")
        sys.exit(1)

    benchmark_files = find_benchmarks(args.path)
    if not benchmark_files:
        print(f"No benchmark files found in '{args.path}'.")
        sys.exit(0)

    # 1. Clear registry to ensure a clean start
    clear_registry()

    for file in benchmark_files:
        try:
            load_benchmarks_safely(file)
        except Exception as e:
            print(f"Error loading benchmarks from '{file}': {e}")
            continue

    # 3. Run benchmarks
    # run_benchmarks will check the registry populated by decorators in the module
    try:
        run_benchmarks(
            max_executions=args.max_executions,
            warmup_executions=args.warmup_executions,
            batch_size=args.batch_size,
            timeout=args.timeout
        )
    except Exception as e:
        print(f"Error during benchmarking: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
