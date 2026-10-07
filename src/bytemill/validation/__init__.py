import os

def validate_pipeline_run(original_count, original_columns, cleaned_df, output_path):
    """
    Validates the integrity of the cleaning job without keeping 
    the original dataframe in memory.
    """
    report = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }

    final_count = len(cleaned_df)
    final_columns = cleaned_df.columns.tolist()

    # 1. Output File Verification
    if not os.path.exists(output_path):
        report["is_valid"] = False
        report["errors"].append(f"Output file missing: {output_path}")
        return report

    if os.path.getsize(output_path) == 0:
        report["is_valid"] = False
        report["errors"].append("Output file is completely empty.")

    # 2. Schema Verification (Did we lose columns?)
    missing_cols = set(original_columns) - set(final_columns)
    if missing_cols:
        report["is_valid"] = False
        report["errors"].append(f"Schema corrupted. Lost columns: {missing_cols}")

    # 3. Row Logic Verification
    if final_count > original_count:
        report["is_valid"] = False
        report["errors"].append("Critical error: Cleaned data has MORE rows than original.")

    if final_count == 0 and original_count > 0:
        report["warnings"].append("Warning: All rows were dropped during cleaning.")

    return report