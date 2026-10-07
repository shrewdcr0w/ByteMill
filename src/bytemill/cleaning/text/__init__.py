import pandas as pd

def strip_whitespace(df):
    """Removes leading/trailing whitespaces from string columns."""
    df_clean = df.copy()
    
    # Find columns that are strings or objects
    text_cols = df_clean.select_dtypes(include=['object', 'string']).columns
    
    for col in text_cols:
        # Strip whitespace, but ignore actual missing values (NaN)
        df_clean[col] = df_clean[col].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )
        
        # Convert pure blank strings "" back to actual None/NaN types
        df_clean[col] = df_clean[col].replace({'': None})
        
    return df_clean