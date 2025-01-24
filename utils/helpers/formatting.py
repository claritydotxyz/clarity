from typing import Any, Dict, List, Union
import json
from datetime import datetime, date
import pandas as pd
import numpy as np

class DataFormatter:
    """Format data for output and display."""
    
    @staticmethod
    def format_json(data: Any) -> str:
        """Format data as JSON string."""
        class CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                if isinstance(obj, (np.int64, np.int32)):
                    return int(obj)
                if isinstance(obj, np.float64):
                    return float(obj)
                if pd.isna(obj):
                    return None
                return super().default(obj)
        
        return json.dumps(data, cls=CustomEncoder, indent=2)

    @staticmethod
    def format_table(data: List[Dict], columns: Optional[List[str]] = None) -> str:
        """Format data as ASCII table."""
        if not data:
            return ""
            
        # Get columns
        cols = columns or list(data[0].keys())
        
        # Get max widths
        widths = {
            col: max(
                len(str(row.get(col, ""))) for row in data + [{"col": col}]
            )
            for col in cols
        }
        
        # Build table
        separator = "-" * (sum(widths.values()) + len(cols) * 3 + 1)
        header = "| " + " | ".join(
            col.ljust(widths[col]) for col in cols
        ) + " |"
        
        rows = []
        for row in data:
            rows.append("| " + " | ".join(
                str(row.get(col, "")).ljust(widths[col])
                for col in cols
            ) + " |")
        
        return "\n".join([separator, header, separator] + rows + [separator])

    @staticmethod
    def format_metrics(metrics: Dict[str, Union[int, float]]) -> str:
        """Format metrics for display."""
        lines = []
        for name, value in metrics.items():
            if isinstance(value, float):
                formatted = f"{value:.2f}"
            else:
                formatted = str(value)
            lines.append(f"{name}: {formatted}")
        return "\n".join(lines)
