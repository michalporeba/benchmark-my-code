from typing import List, Dict, Any
from .model import Benchmark

class BenchmarkResult:
    """A formatted wrapper around the raw Benchmark model, providing zero-dependency CLI and Notebook outputs."""
    
    def __init__(self, benchmark: Benchmark):
        self._benchmark = benchmark
        self.stats = self._extract_stats()

    def _extract_stats(self) -> List[Dict[str, Any]]:
        stats = []
        for func in self._benchmark.functions:
            for variant in func._executions.keys():
                stats.append({
                    "function": func.name,
                    "variant": variant,
                    "executions": len(func.get_executions(variant)),
                    "median_time": func.median_time(variant),
                    "min_time": func.min_time(variant),
                    "max_time": func.max_time(variant),
                })
        return stats

    def __str__(self):
        """Zero-dependency ASCII table formatting for the terminal."""
        if not self.stats:
            return "No benchmark results."
        
        # Try to use rich if installed
        try:
            from rich.console import Console
            from rich.table import Table
            
            table = Table(title="Benchmark Results")
            table.add_column("Function", style="cyan", no_wrap=True)
            table.add_column("Variant", style="magenta")
            table.add_column("Execs", justify="right", style="green")
            table.add_column("Median (s)", justify="right")
            table.add_column("Min (s)", justify="right")

            for s in self.stats:
                table.add_row(
                    s['function'],
                    str(s['variant']),
                    str(s['executions']),
                    f"{s['median_time']:.6f}",
                    f"{s['min_time']:.6f}"
                )
                
            console = Console()
            with console.capture() as capture:
                console.print(table)
            return capture.get()
        except ImportError:
            # Fallback to plain ASCII table
            col_func = max(14, max((len(s["function"]) for s in self.stats), default=14))
            col_var = max(7, max((len(str(s["variant"])) for s in self.stats), default=7))
            
            header = f"{'Function':<{col_func}} | {'Variant':<{col_var}} | {'Execs':<10} | {'Median (s)':<15} | {'Min (s)':<15}"
            divider = "-" * len(header)
            
            lines = [header, divider]
            for s in self.stats:
                lines.append(f"{s['function']:<{col_func}} | {str(s['variant']):<{col_var}} | {s['executions']:<10} | {s['median_time']:<15.6f} | {s['min_time']:<15.6f}")
                
            return "\n".join(lines)

    def _repr_html_(self):
        """Zero-dependency HTML table formatting for Jupyter Notebooks."""
        if not self.stats:
            return "<p>No benchmark results.</p>"
            
        html = ["<table style='border-collapse: collapse; width: 100%; margin-top: 1em;'>"]
        html.append("<thead><tr style='border-bottom: 2px solid #ccc; text-align: left;'>")
        html.append("<th style='padding: 8px;'>Function</th>")
        html.append("<th style='padding: 8px;'>Variant</th>")
        html.append("<th style='padding: 8px; text-align: right;'>Executions</th>")
        html.append("<th style='padding: 8px; text-align: right;'>Median Time (s)</th>")
        html.append("<th style='padding: 8px; text-align: right;'>Min Time (s)</th>")
        html.append("</tr></thead><tbody>")
        
        for s in self.stats:
            html.append("<tr style='border-bottom: 1px solid #eee;'>")
            html.append(f"<td style='padding: 8px; font-weight: bold;'>{s['function']}</td>")
            html.append(f"<td style='padding: 8px;'><code>{s['variant']}</code></td>")
            html.append(f"<td style='padding: 8px; text-align: right;'>{s['executions']}</td>")
            html.append(f"<td style='padding: 8px; text-align: right;'>{s['median_time']:.6f}</td>")
            html.append(f"<td style='padding: 8px; text-align: right;'>{s['min_time']:.6f}</td>")
            html.append("</tr>")
            
        html.append("</tbody></table>")
        return "".join(html)

    # Pass-through methods to maintain backwards compatibility
    @property
    def functions(self):
        return self._benchmark.functions

    def get_function(self, name: str):
        return self._benchmark.get_function(name)
