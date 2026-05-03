from typing import List, Dict, Any
from .model import Benchmark, FailureType

class BenchmarkResult:
    """A formatted wrapper around the raw Benchmark model, providing zero-dependency CLI and Notebook outputs."""
    
    def __init__(self, benchmark: Benchmark):
        self._benchmark = benchmark
        self.hints = [] # List of dicts: {'message': str, 'variant': str, 'stage': str}
        self._cached_stats = None

    @property
    def benchmark(self) -> Benchmark:
        return self._benchmark

    @property
    def stats(self) -> List[Dict[str, Any]]:
        """Dynamically extract current statistics from the underlying model."""
        if self._cached_stats is not None:
            return self._cached_stats
            
        stats_list = []
        for func in self._benchmark.functions:
            # Use list() to prevent RuntimeError if _executions changes size during iteration
            for variant in list(func._executions.keys()):
                stats_list.append({
                    "function": func.name,
                    "variant": variant,
                    "executions": len(func.get_executions(variant)),
                    "median_time": func.median_time(variant),
                    "min_time": func.min_time(variant),
                    "max_time": func.max_time(variant),
                    "status": func.get_status(variant),
                    "peak_memory": func.get_memory(variant)
                })
        self._cached_stats = stats_list
        return stats_list

    def refresh(self) -> None:
        """Clears the cached statistics, forcing a re-calculation on next access."""
        self._cached_stats = None

    def _format_memory(self, bytes_value: float) -> str:
        if bytes_value is None or bytes_value <= 0:
            return "-"
        if bytes_value < 1024:
            return f"{bytes_value:.0f} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        else:
            return f"{bytes_value / (1024 * 1024):.1f} MB"

    def _format_status(self, status: FailureType) -> str:
        if status is None:
            return "UNKNOWN"
        if status == FailureType.NONE:
            return "PASS"
        if status == FailureType.PENDING:
            return "PENDING"
        return status.name

    def __str__(self):
        """Zero-dependency ASCII table formatting for the terminal."""
        current_stats = self.stats # Trigger lazy calculation once
        if not current_stats:
            return "No benchmark results."
        
        output = ""
        # Try to use rich if installed
        try:
            from rich.console import Console
            from rich.table import Table
            
            table = Table(title="Benchmark Results")
            table.add_column("Function", style="cyan", no_wrap=True)
            table.add_column("Variant", style="magenta")
            table.add_column("Execs", justify="right", style="green")
            table.add_column("Median (s)", justify="right")
            table.add_column("Memory", justify="right")
            table.add_column("Status", justify="center")

            for s in current_stats:
                status_str = self._format_status(s['status'])
                style = "green"
                if s['status'] == FailureType.PENDING:
                    style = "yellow"
                elif s['status'] != FailureType.NONE:
                    style = "red"
                
                mem_str = self._format_memory(s['peak_memory'])
                median_str = f"{s['median_time']:.6f}" if s['median_time'] is not None else "-"
                
                table.add_row(
                    s['function'],
                    str(s['variant']),
                    str(s['executions']),
                    median_str,
                    mem_str,
                    f"[{style}]{status_str}[/{style}]"
                )
                
            console = Console()
            with console.capture() as capture:
                console.print(table)
            output = capture.get()
        except ImportError:
            # Fallback to plain ASCII table
            col_func = max(14, max((len(s["function"]) for s in current_stats), default=14))
            col_var = max(7, max((len(str(s["variant"])) for s in current_stats), default=7))
            
            header = f"{'Function':<{col_func}} | {'Variant':<{col_var}} | {'Execs':<10} | {'Median (s)':<12} | {'Memory':<10} | {'Status':<10}"
            divider = "-" * len(header)
            
            lines = [header, divider]
            for s in current_stats:
                status_str = self._format_status(s['status'])
                mem_str = self._format_memory(s['peak_memory'])
                median_val = s['median_time']
                median_str = f"{median_val:<12.6f}" if median_val is not None else f"{'-':<12}"
                lines.append(f"{s['function']:<{col_func}} | {str(s['variant']):<{col_var}} | {s['executions']:<10} | {median_str} | {mem_str:<10} | {status_str:<10}")
            output = "\n".join(lines) + "\n"

        if self.hints:
            output += "\n💡 FEEDBACK:\n"
            for hint in self.hints:
                ctx = ""
                if isinstance(hint, dict):
                    if hint.get('variant') or hint.get('stage'):
                        parts = []
                        if hint.get('stage'): parts.append(f"Stage: {hint['stage']}")
                        if hint.get('variant'): parts.append(f"Variant: {hint['variant']}")
                        ctx = f" ({', '.join(parts)})"
                    output += f"  - {hint['message']}{ctx}\n"
                else:
                    output += f"  - {hint}\n"
        
        return output

    def _repr_html_(self):
        """Zero-dependency HTML table formatting for Jupyter Notebooks."""
        current_stats = self.stats
        if not current_stats:
            return "<p>No benchmark results.</p>"
            
        html = ["<table style='border-collapse: collapse; width: 100%; margin-top: 1em;'>"]
        html.append("<thead><tr style='border-bottom: 2px solid #ccc; text-align: left;'>")
        html.append("<th style='padding: 8px;'>Function</th>")
        html.append("<th style='padding: 8px;'>Variant</th>")
        html.append("<th style='padding: 8px; text-align: right;'>Executions</th>")
        html.append("<th style='padding: 8px; text-align: right;'>Median (s)</th>")
        html.append("<th style='padding: 8px; text-align: right;'>Memory</th>")
        html.append("<th style='padding: 8px; text-align: center;'>Status</th>")
        html.append("</tr></thead><tbody>")
        
        for s in current_stats:
            status_str = self._format_status(s['status'])
            color = "#5cb85c"
            if s['status'] == FailureType.PENDING:
                color = "#f0ad4e"
            elif s['status'] != FailureType.NONE:
                color = "#d9534f"
            
            mem_str = self._format_memory(s['peak_memory'])
            median_str = f"{s['median_time']:.6f}" if s['median_time'] is not None else "-"
            
            html.append("<tr style='border-bottom: 1px solid #eee;'>")
            html.append(f"<td style='padding: 8px; font-weight: bold;'>{s['function']}</td>")
            html.append(f"<td style='padding: 8px;'><code>{s['variant']}</code></td>")
            html.append(f"<td style='padding: 8px; text-align: right;'>{s['executions']}</td>")
            html.append(f"<td style='padding: 8px; text-align: right;'>{median_str}</td>")
            html.append(f"<td style='padding: 8px; text-align: right;'>{mem_str}</td>")
            html.append(f"<td style='padding: 8px; text-align: center; color: white; background-color: {color}; font-size: 0.8em; border-radius: 4px;'>{status_str}</td>")
            html.append("</tr>")
            
        html.append("</tbody></table>")
        
        if self.hints:
            html.append("<div style='background-color: #fcf8e3; border: 1px solid #faebcc; padding: 15px; margin-top: 1em; border-radius: 4px; color: #8a6d3b;'>")
            html.append("<strong>💡 FEEDBACK:</strong>")
            html.append("<ul style='margin-bottom: 0; padding-left: 20px;'>")
            for hint in self.hints:
                ctx = ""
                if isinstance(hint, dict):
                    if hint.get('variant') or hint.get('stage'):
                        parts = []
                        if hint.get('stage'): parts.append(f"<b>{hint['stage']}</b>")
                        if hint.get('variant'): parts.append(f"<code>{hint['variant']}</code>")
                        ctx = f" <small style='color: #666;'>[{' | '.join(parts)}]</small>"
                    html.append(f"<li style='margin-bottom: 5px;'>{hint['message']}{ctx}</li>")
                else:
                    html.append(f"<li>{hint}</li>")
            html.append("</ul></div>")
            
        return "".join(html)

    def to_dict(self) -> List[Dict[str, Any]]:
        """Returns the benchmark statistics as a list of dictionaries."""
        return self.stats

    def to_dataframe(self):
        """
        Attempts to convert stats into a Pandas DataFrame. 
        Requires 'pandas' to be installed.
        """
        try:
            import pandas as pd
            return pd.DataFrame(self.stats)
        except ImportError:
            raise ImportError("Pandas is not installed. Run 'pip install pandas' to use .to_dataframe()")

    # Pass-through methods to maintain backwards compatibility
    @property
    def functions(self):
        return self._benchmark.functions

    def get_function(self, name: str):
        return self._benchmark.get_function(name)
