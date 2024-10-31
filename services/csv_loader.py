# services/csv_loader.py
import os
import glob
import pandas as pd
from typing import Tuple
from datetime import datetime

class CsvLoaderService:
    def __init__(self):
        pass

    def load_latest_csv(self, directory: str) -> Tuple[pd.DataFrame, str, int]:
        """Load the latest CSV file from the specified directory."""
        # Find all CSV files matching our specific pattern (json_cleaned_Xd.csv)
        csv_files = glob.glob(os.path.join(directory, '**', 'json_cleaned_*d.csv'), recursive=True)
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {directory}")
        
        # Print found files for debugging
        print("\nFound CSV files:")
        for file in csv_files:
            print(f"- {file}")
        
        # Get the most recently modified CSV file
        latest_csv = max(csv_files, key=os.path.getmtime)
        latest_directory = os.path.dirname(latest_csv)
        
        print(f"\nSelected latest CSV: {latest_csv}")
        
        # Extract the number of days covered from the filename
        try:
            filename = os.path.basename(latest_csv)
            print(f"Parsing filename: {filename}")
            
            # The filename should be in format 'json_cleaned_Xd.csv' where X is the number of days
            if not filename.startswith('json_cleaned_'):
                raise ValueError(f"Invalid filename format: {filename}. Expected to start with 'json_cleaned_'")
            
            days_part = filename.replace('json_cleaned_', '').split('.')[0]  # Should be like '2d'
            if not days_part.endswith('d'):
                raise ValueError(f"Invalid filename format: {filename}. Expected day part to end with 'd'")
            
            days_str = days_part[:-1]  # Remove the 'd' suffix
            if not days_str.isdigit():
                raise ValueError(f"Invalid day value in filename: {days_str}")
            
            days_covered = int(days_str)
            print(f"Extracted days covered: {days_covered}")
            
        except Exception as e:
            raise ValueError(f"Error parsing days from filename: {e}")
        
        try:
            # Read the CSV file
            df = pd.read_csv(latest_csv)
            print(f"Successfully loaded CSV with {len(df)} rows")
            return df, latest_directory, days_covered
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")
