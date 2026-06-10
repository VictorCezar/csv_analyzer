import pandas as pd
from typing import Dict, Any

class CSVParser:
    """Utility class to parse and inspect CSV files using Pandas."""

    @staticmethod
    def detect_delimiter(file_path: str) -> str:
        """
        Detect the separator/delimiter of a CSV file by counting frequencies of common delimiters.
        """
        possible_delimiters = [',', ';', '\t', '|']
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read up to 5 non-empty lines
                lines = []
                for _ in range(20):
                    line = f.readline()
                    if not line:
                        break
                    if line.strip():
                        lines.append(line)
                        if len(lines) >= 5:
                            break
            if not lines:
                return ','
            
            delim_counts = {d: 0 for d in possible_delimiters}
            for line in lines:
                for d in possible_delimiters:
                    delim_counts[d] += line.count(d)
            
            max_delim = max(delim_counts, key=delim_counts.get)
            if delim_counts[max_delim] > 0:
                return max_delim
        except Exception:
            pass
        return ','

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
            sep = CSVParser.detect_delimiter(file_path)
            return pd.read_csv(file_path, sep=sep, low_memory=False)
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
                            column names, data types, column details/values, and a preview of data.
        """
        columns = list(df.columns)
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        
        col_details = {}
        for col in columns:
            try:
                non_null_vals = df[col].dropna()
                num_unique = non_null_vals.nunique()
                if num_unique == 0:
                    col_details[col] = "All values are missing/null"
                elif df[col].dtype == 'object' or df[col].dtype.name == 'category':
                    if num_unique <= 10:
                        unique_vals = non_null_vals.unique().tolist()
                        col_details[col] = f"Unique values: {unique_vals}"
                    else:
                        sample_vals = non_null_vals.head(5).unique().tolist()
                        col_details[col] = f"Sample values: {sample_vals} (Total unique: {num_unique})"
                else:
                    col_details[col] = f"Numeric (Total unique: {num_unique})"
            except Exception:
                col_details[col] = "Could not analyze column values"
                
        return {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": columns,
            "dtypes": dtypes,
            "col_details": col_details,
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
            details = summary.get("col_details", {}).get(col, "")
            details_str = f" - {details}" if details else ""
            cols_info.append(f"  - {col} ({dtype}){details_str}")
        
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
