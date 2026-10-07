import csv
import chardet
import os

def detect_encoding(file_path, sample_size=100000):
    """Sniffs the file encoding by reading a chunk of raw bytes."""
    with open(file_path, 'rb') as f:
        raw_data = f.read(sample_size)
    result = chardet.detect(raw_data)
    
    # Default to utf-8 if detection confidence is too low
    return result['encoding'] or 'utf-8'

def detect_csv_dialect(file_path, encoding='utf-8', sample_lines=20):
    """Guesses the delimiter, quote character, and if there is a header."""
    with open(file_path, 'r', encoding=encoding) as f:
        # Read a chunk of lines to give the sniffer enough context
        sample = "".join([f.readline() for _ in range(sample_lines)])
        
    try:
        sniffer = csv.Sniffer()
        # Constrain to the most common delimiters to avoid false positives
        dialect = sniffer.sniff(sample, delimiters=[',', ';', '\t', '|'])
        has_header = sniffer.has_header(sample)
        return {
            "delimiter": dialect.delimiter,
            "quotechar": dialect.quotechar,
            "has_header": has_header
        }
    except csv.Error:
        # Fallback to standard CSV if sniffing fails completely
        return {
            "delimiter": ",",
            "quotechar": '"',
            "has_header": True
        }

def inspect_file(file_path):
    """
    Master function to analyze a file before loading it.
    Returns a dictionary of parameters that the reader engine will use.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    file_size = os.path.getsize(file_path)
    encoding = detect_encoding(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    info = {
        "size_bytes": file_size,
        "encoding": encoding,
        "extension": ext
    }
    
    # Only run dialect sniffing on text-based table formats
    if ext in ['.csv', '.tsv', '.txt']:
        dialect_info = detect_csv_dialect(file_path, encoding)
        info.update(dialect_info)
        
    return info