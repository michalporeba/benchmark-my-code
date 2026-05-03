import os
import shutil
import tempfile
import unittest
import subprocess
import sys

class TestCLISideEffects(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_no_top_level_side_effects(self):
        file_path = os.path.join(self.test_dir, "bench_side_effect.py")
        output_file = os.path.join(self.test_dir, "side_effect.txt")
        
        with open(file_path, "w") as f:
            f.write(f"""
from benchmark_my_code import benchit
import os

@benchit
def my_func():
    return True

# This should NOT run
with open(r"{output_file}", "w") as f:
    f.write("I RAN")
""")
        
        # Run benchit CLI
        cmd = ["python3", "-m", "benchmark_my_code.cli", file_path, "--max-executions", "1", "--warmup-executions", "0"]
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        print(result.stdout)
        print(result.stderr)
        
        self.assertEqual(result.returncode, 0)
        self.assertFalse(os.path.exists(output_file), "Side effect file should NOT exist")
        self.assertIn("my_func", result.stdout)

if __name__ == "__main__":
    unittest.main()
