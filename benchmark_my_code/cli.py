import argparse
import importlib.util
import os
import sys
from .api import run_benchmarks, clear_registry

def main():
    parser = argparse.ArgumentParser(prog="benchit", description="Benchmark My Code CLI runner.")
    parser.add_argument("file", help="The Python file to benchmark.")
    # Add other arguments that run_benchmarks supports
    parser.add_argument("--max-executions", type=int, default=100)
    parser.add_argument("--warmup-executions", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=100.0)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    # 1. Clear registry to ensure a clean start
    clear_registry()

    # 2. Import the module to trigger decorators
    module_name = os.path.splitext(os.path.basename(args.file))[0]
    spec = importlib.util.spec_from_file_location(module_name, args.file)
    module = importlib.util.module_from_spec(spec)
    
    # Add the file's directory to sys.path so it can find local imports
    file_dir = os.path.dirname(os.path.abspath(args.file))
    if file_dir not in sys.path:
        sys.path.insert(0, file_dir)
        
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"Error executing module '{args.file}': {e}")
        sys.exit(1)

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
