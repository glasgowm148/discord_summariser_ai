# load_latest_csv.py
import pandas as pd
from pathlib import Path
import re

def load_latest_csv(directory_path):
    print("Identifying the latest directory...")
    directories = [d for d in Path(directory_path).iterdir() if d.is_dir()]
    if not directories:
        raise FileNotFoundError("No directories found in the output directory.")
    latest_directory = max(directories, key=lambda x: x.stat().st_mtime)
    print(f"Latest directory identified: {latest_directory}")

    print("Searching for the latest cleaned CSV file...")
    cleaned_csv_files = list(latest_directory.glob("json_cleaned_*d.csv"))
    if not cleaned_csv_files:
        raise FileNotFoundError("No cleaned CSV files found in the latest directory.")
    latest_file = max(cleaned_csv_files, key=lambda x: x.stat().st_mtime)
    print(f"Latest cleaned CSV file found: {latest_file}")

    # Extract the number of days from the filename
    match = re.search(r"json_cleaned_(\d+)d\.csv", latest_file.name)
    days_covered = int(match.group(1)) if match else None
    print(f"Days covered extracted from filename: {days_covered}")

    print("Reading the CSV file...")
    try:
        df = pd.read_csv(latest_file)
        print(f"CSV file read successfully: {latest_file}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        raise
    return df, latest_directory, days_covered
