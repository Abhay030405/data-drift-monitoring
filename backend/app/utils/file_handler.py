import os
import pandas as pd
from fastapi import UploadFile
from datetime import datetime

# Paths
RAW_DATA_DIR = "data/raw/"
BASELINE_DIR = "data/baseline/"

# Ensure folders exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(BASELINE_DIR, exist_ok=True)

def save_uploaded_file(file: UploadFile):
    """
    Save uploaded file to data/raw/ with timestamp.
    If baseline doesn't exist, also save in baseline/.
    Return metadata including missing values and duplicates.
    """
    filename = file.filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(RAW_DATA_DIR, f"{timestamp}_{filename}")

    # Read file
    if filename.endswith(".csv"):
        df = pd.read_csv(file.file)
    elif filename.endswith(".parquet"):
        df = pd.read_parquet(file.file)
    elif filename.endswith(".json"):
        df = pd.read_json(file.file)
    else:
        raise ValueError("Unsupported file type!")

    # Save to raw
    df.to_csv(save_path, index=False)

    # If baseline empty, save first file as baseline
    if not os.listdir(BASELINE_DIR):
        baseline_path = os.path.join(BASELINE_DIR, filename)
        df.to_csv(baseline_path, index=False)

    # Calculate basic metadata
    metadata = {
        "filename": filename,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "columns_names": df.columns.tolist(),
        "missing_values_count": df.isnull().sum().to_dict(),
        "missing_percentage": (df.isnull().mean()*100).round(2).to_dict(),
        "duplicate_rows": int(df.duplicated().sum())
    }
    return metadata
