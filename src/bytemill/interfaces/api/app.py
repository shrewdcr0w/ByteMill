import os
import sys
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.insert(0, src_dir)

from flask import Flask, request, jsonify, send_from_directory
from bytemill.core.pipeline import ByteMillPipeline

# Detect if we are running as a compiled PyInstaller executable
if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    static_dir = os.path.join(sys._MEIPASS, 'src', 'bytemill', 'interfaces', 'web')
else:
    # Standard Python execution path
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web'))

app = Flask(__name__, static_folder=static_dir, static_url_path='/')

# Configure secure local temporary storage
UPLOAD_FOLDER = os.path.abspath('./temp_workspace/raw')
CLEAN_FOLDER = os.path.abspath('./temp_workspace/clean')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEAN_FOLDER, exist_ok=True)

@app.route('/')
def serve_ui():
    """Serves the main drag-and-drop web interface."""
    return app.send_static_file('index.html')

@app.route('/api/clean', methods=['POST'])
def api_clean():
    """Handles file uploads, format translation, and custom recipes."""
    if 'file' not in request.files:
        return jsonify({"error": "No data file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    # Save uploaded raw file locally
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    # 1. Handle Output Format Translation
    original_ext = os.path.splitext(file.filename)[1]
    output_format = request.form.get('output_format', original_ext)
    
    base_name = os.path.splitext(file.filename)[0]
    output_filename = f"clean_{base_name}{output_format}"
    output_path = os.path.join(CLEAN_FOLDER, output_filename)

    # 2. Parse the Recipe (Prioritize uploaded recipe.json over UI checkboxes)
    recipe = None
    if 'recipe_file' in request.files and request.files['recipe_file'].filename != '':
        recipe_file = request.files['recipe_file']
        try:
            recipe = json.load(recipe_file)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid uploaded recipe.json file"}), 400
    else:
        recipe_json = request.form.get('recipe')
        if recipe_json:
            try:
                recipe = json.loads(recipe_json)
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON recipe from UI"}), 400

    # 3. Run the engine
    try:
        engine = ByteMillPipeline(recipe=recipe)
        stats = engine.run(input_path, output_path)
        
        # Check if the security module generated a PII vault
        vault_name = f"clean_{base_name}_pii_vault.csv"
        has_vault = os.path.exists(os.path.join(CLEAN_FOLDER, vault_name))

        return jsonify({
            "status": "success",
            "stats": stats,
            "download_url": f"/api/download/{output_filename}",
            "vault_url": f"/api/download/{vault_name}" if has_vault else None
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Securely serves the cleaned files back to the browser."""
    return send_from_directory(CLEAN_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    print("Starting ByteMill Local Server on http://localhost:5050")
    app.run(port=5050, debug=True)