# services/csv_loader.py
import os
import glob
import pandas as pd
from typing import Tuple
from services.base_service import BaseService

class CsvLoaderService(BaseService):
    def __init__(self):
        super().__init__()
        self._days_covered = 0
        self._latest_directory = ""

    def load_latest_csv(self, directory: str) -> Tuple[pd.DataFrame, str, int]:
        """Load the latest CSV file from the specified directory."""
        try:
            # Find all CSV files matching our specific pattern (json_cleaned_Xd.csv)
            csv_files = glob.glob(os.path.join(directory, '**', 'json_cleaned_*d.csv'), recursive=True)
            
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {directory}")
            
            # Print found files for debugging
            self.logger.info("\nFound CSV files:")
            for file in csv_files:
                self.logger.info(f"- {file}")
            
            # Get the most recently modified CSV file
            latest_csv = max(csv_files, key=os.path.getmtime)
            self._latest_directory = os.path.dirname(latest_csv)
            
            self.logger.info(f"\nSelected latest CSV: {latest_csv}")
            
            # Extract the number of days covered from the filename
            self._days_covered = self._parse_days_from_filename(latest_csv)
            
            # Read the CSV file
            df = pd.read_csv(latest_csv)
            self.logger.info(f"Successfully loaded CSV with {len(df)} rows")
            return df, self._latest_directory, self._days_covered
            
        except Exception as e:
            self.handle_error(e, {"directory": directory})
            raise

    def _parse_days_from_filename(self, filepath: str) -> int:
        """Parse the number of days covered from the filename."""
        try:
            filename = os.path.basename(filepath)
            self.logger.info(f"Parsing filename: {filename}")
            
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
            self.logger.info(f"Extracted days covered: {days_covered}")
            return days_covered
            
        except Exception as e:
            self.handle_error(e, {"filepath": filepath})
            raise ValueError(f"Error parsing days from filename: {e}") from e

    def get_days_covered(self) -> int:
        """Get the number of days covered by the loaded CSV."""
        return self._days_covered

    def get_latest_directory(self) -> str:
        """Get the directory of the latest loaded CSV."""
        return self._latest_directory

    def initialize(self) -> None:
        """Initialize service-specific resources."""
        pass
