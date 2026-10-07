import pandas as pd
from thefuzz import fuzz

def remove_exact_duplicates(df):
    """
    Scans for rows where every single column matches exactly.
    Returns the cleaned DataFrame and the number of rows removed.
    """
    initial_count = len(df)
    df_clean = df.drop_duplicates(keep='first')
    removed_count = initial_count - len(df_clean)
    
    return df_clean, removed_count

def remove_key_duplicates(df, subset_columns, keep='first'):
    """
    Removes duplicates based on specific identifying columns.
    Useful when a user submits a form twice (same email, different timestamp).
    """
    # Ensure the columns actually exist in the DataFrame to prevent crashes
    valid_columns = [col for col in subset_columns if col in df.columns]
    
    if not valid_columns:
        return df, 0
        
    initial_count = len(df)
    df_clean = df.drop_duplicates(subset=valid_columns, keep=keep)
    removed_count = initial_count - len(df_clean)
    
    return df_clean, removed_count

def remove_fuzzy_duplicates(df, target_column, threshold=90):
    """
    Removes rows where the target column is 90%+ similar to an existing row.
    (e.g., 'Apple Inc' and 'Apple Inc.')
    """
    if target_column not in df.columns:
        return df, 0

    df_clean = df.copy()
    initial_count = len(df_clean)
    
    # Sort by length so we keep the most complete version of the name
    df_clean['length'] = df_clean[target_column].astype(str).str.len()
    df_clean = df_clean.sort_values(by='length', ascending=False).drop(columns=['length'])
    
    kept_indices = []
    seen_values = []
    
    for idx, val in df_clean[target_column].items():
        if pd.isna(val):
            kept_indices.append(idx)
            continue
            
        val_str = str(val)
        is_duplicate = False
        
        for seen in seen_values:
            # Compare similarity using TheFuzz
            if fuzz.token_sort_ratio(val_str, seen) >= threshold:
                is_duplicate = True
                break
                
        if not is_duplicate:
            seen_values.append(val_str)
            kept_indices.append(idx)
            
    df_clean = df_clean.loc[kept_indices]
    removed_count = initial_count - len(df_clean)
    
    return df_clean, removed_count