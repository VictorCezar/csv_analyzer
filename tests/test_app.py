import os
import pytest
import math
import numpy as np
from fastapi.testclient import TestClient
from app import app, sanitize_for_json

client = TestClient(app)

def test_sanitize_for_json():
    data = {
        "nan_val": float("nan"),
        "inf_val": float("inf"),
        "neg_inf_val": float("-inf"),
        "normal_val": 42.0,
        "list_val": [float("nan"), 10],
        "dict_val": {"nested_nan": float("nan")},
        "numpy_nan": np.nan,
        "numpy_int": np.int64(123),
        "numpy_float": np.float64(3.14),
    }
    
    sanitized = sanitize_for_json(data)
    assert sanitized["nan_val"] is None
    assert sanitized["inf_val"] is None
    assert sanitized["neg_inf_val"] is None
    assert sanitized["normal_val"] == 42.0
    assert sanitized["list_val"] == [None, 10]
    assert sanitized["dict_val"] == {"nested_nan": None}
    assert sanitized["numpy_nan"] is None
    assert sanitized["numpy_int"] == 123
    assert sanitized["numpy_float"] == 3.14

def test_api_upload_with_nan(tmp_path):
    # Create a CSV with a missing value (which pandas loads as NaN)
    csv_file = tmp_path / "test_nan.csv"
    csv_file.write_text("name,age,salary\nAlice,30,60000\nBob,35,\nCharlie,28,80000\n")
    
    import app as app_mod
    original_data_dir = app_mod.DATA_DIR
    app_mod.DATA_DIR = str(tmp_path)
    
    try:
        with open(csv_file, "rb") as f:
            response = client.post("/api/upload", files={"file": ("test_nan.csv", f, "text/csv")})
            
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["filename"] == "test_nan.csv"
        assert json_data["num_rows"] == 3
        
        # Check preview
        preview = json_data["preview"]
        assert len(preview) == 3
        # Bob's salary should be None (JSON null) instead of nan
        assert preview[0]["salary"] == 60000
        assert preview[1]["salary"] is None
        assert preview[2]["salary"] == 80000
    finally:
        app_mod.DATA_DIR = original_data_dir
