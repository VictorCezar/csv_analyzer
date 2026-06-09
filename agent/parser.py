import pandas as pd
from typing import Dict, Any

class CSVParser:
    """Utility class to parse and inspect CSV files using Pandas."""

    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        """
        Load a CSV file into a Pandas DataFrame.
        
        Args:
            file_path: The filesystem path to the CSV file.
            
        Returns:
            pd.DataFrame: The parsed CSV data.
            
        Raises:
            ValueError: If the file cannot be loaded or parsed.
        """
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file at {file_path}: {e}")

    @staticmethod
    def get_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a structured dictionary summary of the DataFrame.
        
        Args:
            df: The Pandas DataFrame to summarize.
            
        Returns:
            Dict[str, Any]: A dictionary containing row count, column count, 
                            column names, data types, and a preview of data.
        """
        return {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview": df.head(3).to_dict(orient="records"),
        }

    @staticmethod
    def format_summary_for_llm(summary: Dict[str, Any]) -> str:
        """
        Format the summary dictionary into a clean string for LLM prompts.
        
        Args:
            summary: The summary dictionary from get_summary.
            
        Returns:
            str: A formatted text representation of the CSV structure.
        """
        cols_info = []
        for col in summary["columns"]:
            dtype = summary["dtypes"][col]
            cols_info.append(f"  - {col} ({dtype})")
        
        preview_rows = []
        for i, row in enumerate(summary["preview"]):
            preview_rows.append(f"    Row {i+1}: {row}")
            
        return (
            f"CSV Metadata:\n"
            f"- Total Rows: {summary['num_rows']}\n"
            f"- Total Columns: {summary['num_columns']}\n"
            f"- Schema:\n" + "\n".join(cols_info) + "\n"
            f"- Data Preview (first {len(summary['preview'])} rows):\n" + "\n".join(preview_rows)
        )
