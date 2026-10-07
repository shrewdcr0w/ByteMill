import pandas as pd

def normalize_nulls(df, profile, text_fill="Unknown", num_fill=0):
    """
    Fills missing values intelligently using the profiler's data type guesses.
    """
    df_clean = df.copy()
    
    for col, stats in profile["columns"].items():
        if stats["null_count"] > 0:
            col_type = stats["inferred_type"]
            
            # If it's a text/categorical column, fill with "Unknown"
            if col_type in ["string", "object", "mixed"]:
                df_clean[col] = df_clean[col].fillna(text_fill)
                
            # If it's a numeric column, fill with 0 (or you could use mean/median)
            elif col_type in ["floating", "integer", "numeric"]:
                df_clean[col] = df_clean[col].fillna(num_fill)
                
    return df_clean