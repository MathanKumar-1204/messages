import os
from flask import Flask, jsonify, render_template
from processor import process_jsonl_file

app = Flask(__name__, template_folder="templates")

SAMPLE_FILE_PATH = os.getenv("SAMPLE_FILE_PATH", "sample_messages.jsonl")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/summary", methods=["GET"])
def get_summary():
    try:
        result = process_jsonl_file(SAMPLE_FILE_PATH)
        return jsonify(result), 200
    except FileNotFoundError:
        return jsonify({"error": "Sample file not found", "path": SAMPLE_FILE_PATH}), 404
    except Exception as e:
        return jsonify({"error": "Failed to read device messages file", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
