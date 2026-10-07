import pandas as pd
import os
import csv

def read_file_chunks(file_path, chunk_size=100000, **kwargs):
    """Reads massive files in chunks and logs malformed rows."""
    
    ext = str(file_path).lower()
    
    # 1. Define the logging function for broken rows
    def log_bad_line(bad_line):
        # The 'a' stands for Append Mode. It adds rows without overwriting.
        with open('error_log.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(bad_line)
            
    try:
        if ext.endswith('.csv'):
            # Clear the old log if it exists before a new run
            if os.path.exists('error_log.csv'):
                os.remove('error_log.csv')
                
            return pd.read_csv(
                file_path, 
                chunksize=chunk_size,
                on_bad_lines=log_bad_line, 
                low_memory=True,
                engine='python'
            )
            
        elif ext.endswith('.json'):
            return pd.read_json(file_path, lines=True, chunksize=chunk_size)
                    
        elif ext.endswith('.xls') or ext.endswith('.xlsx'):
            print("   [!] Note: Excel files do not support chunking. Loading entirely into memory.")
            return [pd.read_excel(file_path, engine='openpyxl')]
            
        else:
            raise ValueError(f"Unsupported file format: {ext}")
            
    except Exception as e:
        raise RuntimeError(f"Failed to read {ext} file in chunks: {str(e)}")