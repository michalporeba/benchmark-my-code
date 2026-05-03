import os
import shutil
import tempfile
import unittest
from benchmark_my_code.cli import find_benchmarks

class TestCLIDiscovery(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_find_benchmarks_single_file(self):
        file_path = os.path.join(self.test_dir, "bench_me.py")
        with open(file_path, "w") as f:
            f.write("@benchit\ndef my_func(): pass")
        
        found = find_benchmarks(file_path)
        self.assertEqual(found, [file_path])
        
    def test_find_benchmarks_directory(self):
        os.makedirs(os.path.join(self.test_dir, "subdir"))
        file1 = os.path.join(self.test_dir, "bench1.py")
        file2 = os.path.join(self.test_dir, "subdir", "bench2.py")
        other = os.path.join(self.test_dir, "not_a_bench.txt")
        
        for p in [file1, file2, other]:
            with open(p, "w") as f:
                if "bench" in p:
                    f.write("@benchit\ndef func(): pass")
                else:
                    f.write("pass")
                
        found = sorted(find_benchmarks(self.test_dir))
        self.assertEqual(found, sorted([file1, file2]))

    def test_find_benchmarks_skips_no_bench(self):
        file_path = os.path.join(self.test_dir, "no_bench.py")
        with open(file_path, "w") as f:
            f.write("def my_func(): pass")
        
        found = find_benchmarks(file_path)
        self.assertEqual(found, [])

if __name__ == "__main__":
    unittest.main()
