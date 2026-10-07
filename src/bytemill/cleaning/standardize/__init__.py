import pandas as pd
import numpy as np
from difflib import get_close_matches

def normalize_dates(df):
    """Converts any identifiable date column into ISO 8601 format (YYYY-MM-DD)."""
    df_clean = df.copy()
    for col in df_clean.columns:
        # Check if column name suggests dates
        if any(k in str(col).lower() for k in ['date', 'time', 'dob']):
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce').dt.strftime('%Y-%m-%d')
    return df_clean

def standardize_addresses(df):
    """Expands common address abbreviations for consistency."""
    df_clean = df.copy()
    address_cols = [col for col in df.columns if 'address' in str(col).lower()]
    
    replacements = {
        r'\bSt\.?\b': 'Street',
        r'\bAve\.?\b': 'Avenue',
        r'\bRd\.?\b': 'Road',
        r'\bApt\.?\b': 'Apartment',
        r'\bBlvd\.?\b': 'Boulevard'
    }
    
    for col in address_cols:
        df_clean[col] = df_clean[col].replace(replacements, regex=True)
    return df_clean

def cluster_categories(df):
    """Finds slightly misspelled categories and standardizes them to the most common variation."""
    df_clean = df.copy()
    # Only target string columns with low cardinality (likely categories)
    cat_cols = [col for col in df.select_dtypes(include=['object']).columns if df[col].nunique() < 50]
    
    for col in cat_cols:
        value_counts = df_clean[col].value_counts()
        if value_counts.empty: continue
        
        # Use the most frequent item as the base truth
        valid_categories = value_counts.index.astype(str).tolist()
        
        def match_category(val):
            if pd.isna(val) or val == "Unknown": return val
            matches = get_close_matches(str(val), valid_categories, n=1, cutoff=0.85)
            return matches[0] if matches else val
            
        df_clean[col] = df_clean[col].apply(match_category)
    return df_clean

def detect_outliers_zscore(df, threshold=3.0):
    """Flags numeric values that deviate by more than 3 standard deviations from the mean."""
    df_clean = df.copy()
    num_cols = df_clean.select_dtypes(include=[np.number]).columns
    
    for col in num_cols:
        mean = df_clean[col].mean()
        std = df_clean[col].std()
        if std > 0:
            # Add a boolean flag column instead of deleting the data
            df_clean[f"{col}_is_outlier"] = np.abs((df_clean[col] - mean) / std) > threshold
    return df_clean