from flask import Flask, render_template, request, send_file, jsonify
from docx import Document
import os
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/generate", methods=["POST"])
def generate():
    # Your quotation logic (same as before, unchanged)
    return send_file("your-output-file.docx", as_attachment=True)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    if not message:
        return jsonify({"reply": "No message received."})

    api_key = os.environ.get("HF_API_KEY")
    if not api_key:
        return jsonify({"reply": "Hugging Face API key not set."})

    payload = {
        "inputs": f"<s>[INST] {message} [/INST]",
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 300
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        hf_response = response.json()

        # Handle HF response format
        if isinstance(hf_response, list) and "generated_text" in hf_response[0]:
            reply = hf_response[0]["generated_text"].replace(f"<s>[INST] {message} [/INST]", "").strip()
        else:
            reply = hf_response.get("error", "No response received.")

        return jsonify({"reply": reply})

    except requests.exceptions.RequestException as e:
        return jsonify({"reply": f"DSV Bot Error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
