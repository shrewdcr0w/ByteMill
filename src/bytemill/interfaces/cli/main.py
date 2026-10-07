import argparse
import json
import sys
from bytemill.core.pipeline import ByteMillPipeline

def cli_main():
    parser = argparse.ArgumentParser(description="ByteMill - Local-first Data Cleaning Engine")
    parser.add_argument("input", help="Path to the raw input file (CSV, TSV, etc.)")
    parser.add_argument("output", help="Path where the clean file should be saved")
    parser.add_argument("--recipe", help="Optional: Path to a JSON recipe file to override default rules", default=None)
    
    args = parser.parse_args()
    
    # 1. Load custom recipe if provided
    recipe_config = None
    if args.recipe:
        try:
            with open(args.recipe, 'r') as f:
                recipe_config = json.load(f)
            print(f" Loaded custom recipe: {args.recipe}")
        except Exception as e:
            print(f" Error loading recipe: {e}")
            sys.exit(1)
    
    # 2. Run the engine
    try:
        engine = ByteMillPipeline(recipe=recipe_config)
        engine.run(args.input, args.output)
    except Exception as e:
        print(f" Pipeline Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli_main()