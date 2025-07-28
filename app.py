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
    return send_file("your-output-file.docx", as_attachment=True)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"reply": "No message received."})

    hf_token = os.environ.get("HF_API_KEY")
    if not hf_token:
        return jsonify({"reply": "❌ Hugging Face API key not configured."})

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": f"<s>[INST] {message} [/INST]",
        "parameters": {
            "temperature": 0.4,
            "max_new_tokens": 300,
            "top_p": 0.95,
            "repetition_penalty": 1.1,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            reply = result[0]["generated_text"].strip()
        else:
            reply = result.get("error", "No valid response received.")

        return jsonify({"reply": reply})

    except requests.exceptions.RequestException as e:
        return jsonify({"reply": f"DSV Bot Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
