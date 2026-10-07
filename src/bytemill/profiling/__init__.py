import pandas as pd
import numpy as np

def profile_dataframe(df):
    """
    Scans a DataFrame and returns a dictionary of column statistics.
    Identifies types, null counts, and uniqueness.
    """
    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": {}
    }

    for col in df.columns:
        col_data = df[col]
        
        # Basic stats
        null_count = col_data.isna().sum()
        unique_count = col_data.nunique()
        
        # Infer the actual data type (vs what pandas defaulted to)
        inferred_type = pd.api.types.infer_dtype(col_data, skipna=True)
        
        # Calculate percentages
        p_null = (null_count / len(df)) * 100 if len(df) > 0 else 0
        p_unique = (unique_count / len(df)) * 100 if len(df) > 0 else 0
        
        # Semantic guessing (Is it an ID? Is it categorical?)
        is_categorical = False
        if inferred_type in ['string', 'object']:
            # If a text column has very few unique values, it's likely a category
            if unique_count < 20 and p_unique < 10:
                is_categorical = True
        
        profile["columns"][col] = {
            "inferred_type": inferred_type,
            "null_count": int(null_count),
            "null_percent": round(p_null, 2),
            "unique_count": int(unique_count),
            "unique_percent": round(p_unique, 2),
            "is_categorical": is_categorical
        }

    return profile