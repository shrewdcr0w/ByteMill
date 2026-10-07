# ByteMill: Local-First Data Cleaning Engine

**Version:** 1.0.0
**Architecture:** Python / Pandas / Flask

ByteMill is a high-performance, robust, and completely offline data cleaning engine. It is designed to process massive datasets (5GB+) on standard consumer hardware without running out of memory. It provides both a Command Line Interface (CLI) for developers and a standalone local Web UI for end users.

---

## Table of Contents

1. [Core Principles and Capabilities](#1-core-principles-and-capabilities)
2. [Setup and Installation](#2-setup-and-installation)
3. [Directory Structure and Module Reference](#3-directory-structure-and-module-reference)
4. [Usage: Command Line Interface](#4-usage-command-line-interface)
5. [Usage: Web Interface](#5-usage-web-interface)
6. [The Recipe Engine](#6-the-recipe-engine)
7. [System Limitations and Known Constraints](#7-system-limitations-and-known-constraints)
---

## 1. Core Principles and Capabilities

1. **Non-destructive by design.** ByteMill never overwrites the source file. It reads the input and writes to an explicitly defined output destination.
2. **Infinite scaling (streaming).** A chunked generator architecture (100,000 rows at a time) keeps RAM usage flat, allowing low-spec laptops to process very large CSV and JSON files.
3. **Format agnostic.** Automatically routes and processes `.csv`, `.json`, `.xls`, and `.xlsx` files without user intervention.
4. **Global deduplication.** Maintains a lightweight 64-bit hash set in memory to catch exact and key-based duplicates across the entire file, even between distant chunks.
5. **PII security vault.** Masks or cryptographically hashes Personally Identifiable Information (PII) and generates an isolated "Vault" CSV that maps the original values to the redacted values.

---

## 2. Setup and Installation

ByteMill is built in Python. To prevent conflicts with other projects on your computer, run it inside an isolated virtual environment (venv).

### Step 1: Create and activate the virtual environment

Open a terminal in the root project directory and run the commands for your operating system.

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install dependencies

With the environment active, run:

```bash
pip install -r requirements.txt
```

`requirements.txt` includes:

| Package | Purpose |
|---|---|
| `pandas` | Core data manipulation |
| `openpyxl` | Excel read/write support |
| `thefuzz`, `chardet` | Fuzzy string matching and encoding detection |
| `Flask`, `Werkzeug` | Local Web UI server |
| `pytest`, `pyinstaller` | Testing and executable compilation |

---

## 3. Directory Structure and Module Reference

```text
ByteMill/
|
|-- requirements.txt
|-- venv/                          # Virtual environment (ignored in git)
|-- docs/                          # Project documentation
|
|-- src/
    |-- bytemill/
        |-- core/
        |   |-- pipeline.py        # Master orchestrator. Handles chunking and global dedupe.
        |
        |-- cleaning/
        |   |-- dedupe.py          # Exact, key-based, and fuzzy deduplication.
        |   |-- security/          # PII masking, hashing, and vault generation.
        |   |-- standardize.py     # Dates, addresses, categories, outlier detection.
        |   |-- text.py            # Whitespace stripping.
        |   |-- types.py           # Intelligent null-filling based on column types.
        |
        |-- io/
        |   |-- readers.py         # Chunk generators and format routers (CSV, JSON, Excel).
        |   |-- detect.py          # Encoding and delimiter detection.
        |
        |-- profiling/
        |   |-- __init__.py        # Inspects data types and null distributions.
        |
        |-- validation/
        |   |-- __init__.py        # Row reconciliation and integrity checks after cleaning.
        |
        |-- interfaces/
            |-- api/
            |   |-- app.py         # Flask server linking the Web UI to the pipeline.
            |-- cli/
            |   |-- main.py        # argparse implementation for terminal execution.
            |-- web/
                |-- index.html     # Drag-and-drop frontend UI.
```

---

## 4. Usage: Command Line Interface

The CLI is designed for data engineers and automated ETL scripts.

### Basic execution

```bash
python src/bytemill/interfaces/cli/main.py data/messy_data.csv data/clean_data.csv
```

This runs the engine with the **Default Recipe**:

- Strips whitespace
- Normalizes nulls
- Removes exact duplicates
- No PII masking

### Execution with a custom recipe

To apply specific rules, pass a JSON recipe file:

```bash
python src/bytemill/interfaces/cli/main.py data/input.csv data/output.csv --recipe my_rules.json
```

---

## 5. Usage: Web Interface

The Web UI allows non-technical users to clean data through a drag-and-drop browser interface.

### Starting the server

```bash
python src/bytemill/interfaces/api/app.py
```

### Using the interface

1. Open your browser to `http://localhost:5050`.
2. Drag and drop your `.csv`, `.json`, or `.xlsx` file.
3. Check the rule boxes in the UI. These automatically generate a recipe in the background.
4. Click **PROCESS**.
5. Download the clean file (and the PII Vault, if security was enabled).

> **Note:** Files processed through the Web UI are temporarily stored in `./temp_workspace/raw` and `./temp_workspace/clean`. These folders must be cleared manually from time to time.

---

## 6. The Recipe Engine

ByteMill is strictly deterministic. It only does what the recipe tells it to do.

### Building a custom recipe

Create a file named `custom_recipe.json`. Every key acts as an on/off switch or configuration for a specific cleaning module.

```json
{
  "strip_whitespace": true,
  "normalize_nulls": true,
  "text_fill_value": "Unknown",
  "num_fill_value": 0.0,
  "normalize_dates": true,
  "standardize_addresses": true,
  "cluster_categories": false,
  "detect_outliers": true,

  "deduplicate_exact": true,
  "deduplicate_keys": ["email", "phone_number"],
  "deduplicate_fuzzy": "company_name",

  "pii_masking": {
    "method": "hash",
    "columns": ["ssn", "credit_card", "password"]
  }
}
```

### Module definitions

| Key | Description |
|---|---|
| `normalize_nulls` | Replaces NaN with `text_fill_value` for strings and `num_fill_value` for numbers. |
| `deduplicate_keys` | Removes rows where the specified columns match (for example, duplicate emails), keeping only the first instance. |
| `deduplicate_fuzzy` | Uses Levenshtein distance (TheFuzz) to find 90%+ string matches in the target column (for example, "Apple Inc" vs "Apple Inc."). |
| `pii_masking.method` | Accepts `"mask"` (replaces values with `REDACTED`) or `"hash"` (replaces values with a one-way SHA-256 fingerprint). |

---

## 7. System Limitations and Known Constraints

Version 1.0 has the following architectural boundaries.

### Excel chunking is not possible

The `.xlsx` format is a zipped XML directory, not a flat text file, so it cannot be read in chunks. If a user uploads an Excel file, ByteMill bypasses the chunk generator and loads the entire file into RAM.

Do not process 5GB Excel files on a laptop with 8GB of RAM. Convert the file to CSV first.

### Chunk-level fuzzy deduplication

- **Exact and key-based matches** are checked globally across the entire file using memory-efficient 64-bit integer hashes.
- **Fuzzy deduplication** is restricted to the chunk level (per 100,000 rows). Comparing strings globally across 50 million rows requires O(N^2) complexity and a vector database, which exceeds desktop hardware limits.

### No cell-level audit trail

The PII Vault tracks exact before-and-after values for security purposes, but the engine does not log cell-level changes (for example, "Row 5, Col 2: Removed leading space"). Doing so in Pandas degrades streaming performance by over 80%.
python src/bytemill/interfaces/api/app.py
