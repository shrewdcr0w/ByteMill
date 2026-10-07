import pandas as pd
import hashlib

def mask_pii(df, target_columns=None, method="mask"):
    """
    Secures Personally Identifiable Information (PII) using masking or hashing.
    Returns the cleaned DataFrame, the affected columns, and a Vault DataFrame 
    containing the mapping of original values to secured values.
    """
    df_clean = df.copy()
    masked_cols = []
    vault_records = []

    # Auto-detect PII if no specific columns are provided
    if not target_columns:
        pii_keywords = ['email', 'phone', 'ssn', 'password', 'credit', 'dob', 'address']
        target_columns = [col for col in df.columns if any(k in str(col).lower() for k in pii_keywords)]

    valid_cols = [col for col in target_columns if col in df.columns]

    for col in valid_cols:
        masked_cols.append(col)
        
        # Iterate through the column to build the mapping vault
        for idx, val in df_clean[col].items():
            if pd.isna(val) or str(val).strip() == "":
                continue
                
            val_str = str(val)
            
            if method == "hash":
                # Irreversible cryptographic hash (HIPAA/GDPR compliant tracking)
                secured_val = hashlib.sha256(val_str.encode()).hexdigest()
            else:
                # Standard visual masking
                secured_val = "REDACTED"
                
            vault_records.append({
                "column": col,
                "original_value": val_str,
                "secured_value": secured_val
            })
            
            # Apply the secured value to the actual dataframe
            df_clean.at[idx, col] = secured_val

    # Convert the records into a DataFrame for the pipeline to export
    vault_df = pd.DataFrame(vault_records)
    
    # Drop duplicates in the vault so we only store unique mappings
    if not vault_df.empty:
        vault_df = vault_df.drop_duplicates()

    return df_clean, masked_cols, vault_df