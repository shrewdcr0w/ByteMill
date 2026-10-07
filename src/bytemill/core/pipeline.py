import os
import pandas as pd
from bytemill.cleaning.dedupe import remove_fuzzy_duplicates
from bytemill.cleaning.standardize import normalize_dates, standardize_addresses, cluster_categories, detect_outliers_zscore
from bytemill.io.detect import inspect_file
from bytemill.validation import validate_pipeline_run
from bytemill.cleaning.security import mask_pii
from bytemill.io.readers import read_file_chunks
from bytemill.profiling import profile_dataframe
from bytemill.cleaning.text import strip_whitespace
from bytemill.cleaning.types import normalize_nulls

class ByteMillPipeline:
    def __init__(self, recipe=None):
        # If no custom JSON recipe is provided, the engine defaults 
        # to standard, non-destructive cleaning with NO cryptography.
        self.recipe = recipe or {
            "strip_whitespace": True,
            "normalize_nulls": True,
            "text_fill_value": "Unknown",
            "num_fill_value": 0.0,
            "deduplicate_exact": True,
            "deduplicate_keys": [],
            "pii_masking": False  # Security is OFF by default
        }

    def run(self, input_path, output_path, chunk_size=100000):
        """Executes the standard pipeline using a low-memory streaming architecture."""
        print(f"Starting ByteMill Pipeline for: {input_path}")
        
        file_info = inspect_file(input_path)
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            
        ext = os.path.splitext(output_path)[1].lower()
        
        total_ingested = 0
        total_final = 0
        original_columns = []
        is_first_chunk = True

        # Initialize Global Memory Sets for cross-chunk deduplication
        seen_exact_hashes = set()
        seen_key_values = set()

        # Loop through the file in chunks
        for chunk_idx, df in enumerate(read_file_chunks(input_path, chunk_size=chunk_size)):
            chunk_rows = len(df)
            total_ingested += chunk_rows
            print(f"   [+] Processing Block {chunk_idx + 1} ({chunk_rows} rows)...")
            
            if is_first_chunk:
                original_columns = df.columns.tolist()

            # 1. Profile
            profile = profile_dataframe(df)

            # 2. Clean (Apply standardizers first so deduplication works on clean data)
            if self.recipe.get("strip_whitespace"):
                df = strip_whitespace(df)
            if self.recipe.get("normalize_nulls"):
                df = normalize_nulls(df, profile, text_fill=self.recipe.get("text_fill_value", "Unknown"), num_fill=self.recipe.get("num_fill_value", 0.0))
            if self.recipe.get("normalize_dates"):
                df = normalize_dates(df)
            if self.recipe.get("standardize_addresses"):
                df = standardize_addresses(df)
            if self.recipe.get("cluster_categories"):
                df = cluster_categories(df)
            if self.recipe.get("detect_outliers"):
                df = detect_outliers_zscore(df)
                
            # 3. Global Deduplication Logic
            if self.recipe.get("deduplicate_exact"):
                # Generate a 64-bit integer fingerprint for every row
                row_hashes = pd.util.hash_pandas_object(df, index=False)
                mask = ~row_hashes.isin(seen_exact_hashes)
                removed = len(df) - mask.sum()
                if removed > 0:
                    print(f"   [+] Dropped {removed} global exact duplicates.")
                
                df = df[mask]
                seen_exact_hashes.update(row_hashes[mask])

            dedupe_keys = self.recipe.get("deduplicate_keys", [])
            if dedupe_keys and all(k in df.columns for k in dedupe_keys):
                # Combine the target keys into a single string for tracking
                key_series = df[dedupe_keys].astype(str).agg('-'.join, axis=1)
                mask = ~key_series.isin(seen_key_values)
                removed = len(df) - mask.sum()
                if removed > 0:
                    print(f"   [+] Dropped {removed} global key duplicates.")
                
                df = df[mask]
                seen_key_values.update(key_series[mask])

            # Chunk-level Fuzzy Deduplication
            fuzzy_col = self.recipe.get("deduplicate_fuzzy")
            if fuzzy_col:
                df, removed = remove_fuzzy_duplicates(df, fuzzy_col)
                if removed > 0:
                    print(f"   [+] Removed {removed} fuzzy duplicates (chunk-level).")

            # 4. PII Security
            pii_policy = self.recipe.get("pii_masking")
            if pii_policy:
                method = pii_policy.get("method", "mask")
                cols = pii_policy.get("columns", None)
                df, masked_cols, vault_df = mask_pii(df, target_columns=cols, method=method)
                
                # Append vault data securely
                if not vault_df.empty:
                    vault_path = output_path.replace(ext, "_pii_vault.csv")
                    vault_mode = 'w' if is_first_chunk else 'a'
                    vault_df.to_csv(vault_path, index=False, mode=vault_mode, header=is_first_chunk)

            total_final += len(df)

            # 5. Export Chunk (Append to output file)
            mode = 'w' if is_first_chunk else 'a'
            header = is_first_chunk
            
            if ext == '.json':
                df.to_json(output_path, orient='records', lines=True, mode=mode)
            elif ext in ['.xls', '.xlsx']:
                if not is_first_chunk:
                    print("   [!] Warning: Excel does not support chunked appending. Output may be incomplete.")
                df.to_excel(output_path, index=False)
            else:
                df.to_csv(output_path, index=False, mode=mode, header=header)

            is_first_chunk = False

        print(f"   [+] Clean file saved to: {output_path}")

        # 6. Validate the Result
        validation_report = validate_pipeline_run(total_ingested, original_columns, df, output_path)

        if not validation_report["is_valid"]:
            print("   [!] VALIDATION FAILED:")
            for error in validation_report["errors"]:
                print(f"       - {error}")
        else:
            print("   [+] Validation passed. Data integrity verified.")

        print("Pipeline complete!")
        return {
            "original_rows": total_ingested, 
            "final_rows": total_final,
            "is_valid": validation_report["is_valid"]
        }