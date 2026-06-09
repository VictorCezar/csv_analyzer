import os
import pandas as pd
import pytest
from agent.parser import CSVParser

@pytest.fixture
def sample_csv_path(tmp_path):
    """Fixture to create a temporary sample CSV file."""
    csv_file = tmp_path / "test.csv"
    data = (
        "name,age,salary\n"
        "Alice,30,60000\n"
        "Bob,35,90000\n"
        "Charlie,28,80000\n"
    )
    csv_file.write_text(data)
    return str(csv_file)

def test_load_csv(sample_csv_path):
    df = CSVParser.load_csv(sample_csv_path)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert list(df.columns) == ["name", "age", "salary"]

def test_load_csv_invalid_path():
    with pytest.raises(ValueError):
        CSVParser.load_csv("non_existent_file.csv")

def test_get_summary(sample_csv_path):
    df = CSVParser.load_csv(sample_csv_path)
    summary = CSVParser.get_summary(df)
    
    assert summary["num_rows"] == 3
    assert summary["num_columns"] == 3
    assert summary["columns"] == ["name", "age", "salary"]
    assert "name" in summary["dtypes"]
    assert len(summary["preview"]) == 3

def test_format_summary_for_llm(sample_csv_path):
    df = CSVParser.load_csv(sample_csv_path)
    summary = CSVParser.get_summary(df)
    formatted = CSVParser.format_summary_for_llm(summary)
    
    assert "Total Rows: 3" in formatted
    assert "Total Columns: 3" in formatted
    assert "Schema:" in formatted
    assert "name" in formatted
    assert "age" in formatted
    assert "salary" in formatted
