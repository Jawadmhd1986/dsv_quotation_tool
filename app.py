from flask import Flask, render_template, request, send_file, jsonify
from docx import Document
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/generate", methods=["POST"])
def generate():
    # Minimal fallback doc file (you can enhance with template logic later)
    return send_file("templates/Standard VAS.docx", as_attachment=True)

# ✅ Fully Offline Chatbot
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower().strip()

    faq = {
        "hi": "Hello! How can I help you today?",
        "hello": "Hi there! Ask me anything about DSV warehousing, logistics or transport.",
        "who are you": "I am DSV Assistant, here to help you with all warehousing, storage, and transport queries.",
        "what is dsv": "DSV is a global logistics company providing transport, warehousing, and supply chain solutions.",
        "ac storage rate": "AC storage is charged at 2.5 AED per CBM per day.",
        "non-ac storage rate": "Non-AC storage is 2.0 AED per CBM per day.",
        "open shed rate": "Open Shed storage is 1.8 AED per CBM per day.",
        "chemical ac rate": "Chemical AC storage is 3.5 AED per CBM per day.",
        "chemical non-ac rate": "Chemical Non-AC is 2.7 AED per CBM per day.",
        "open yard mussafah": "Mussafah open yard rate is 160 AED per SQM per year.",
        "open yard kizad": "KIZAD open yard rate is 125 AED per SQM per year.",
        "wms charge": "WMS (Warehouse Management System) is charged at 1500 AED per month unless it's Open Yard.",
        "minimum storage": "The minimum monthly storage fee is 3500 AED.",
        "dsv services": "DSV offers warehousing, customs clearance, air & ocean freight, and fleet-based transportation.",
        "what does dsv offer": "DSV provides full logistics services including warehousing, transport, and supply chain solutions in the UAE and globally.",
        "greeting": "Welcome to DSV UAE. How may I assist you today?",
        "contact": "You can contact the DSV UAE team via email, phone, or our official website.",
        "thank you": "You're most welcome! 😊",
        "thanks": "Glad to assist. Let me know if you have more questions!",
        "bye": "Goodbye! Have a great day!",
        "who owns dsv": "DSV A/S is a publicly traded company headquartered in Denmark."
    }

    # Match by keyword (optional improvement)
    for key in faq:
        if key in message:
            return jsonify({"reply": faq[key]})

    # Default fallback
    fallback = "I'm sorry, I didn't understand that. You can ask about DSV storage types, WMS, or logistics services."
    return jsonify({"reply": fallback})

if __name__ == "__main__":
    app.run(debug=True)
