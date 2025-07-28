from flask import Flask, render_template, request, send_file, jsonify
from docx import Document
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/generate", methods=["POST"])
def generate():
    # Keep your existing quotation logic here (not changed)
    return send_file("templates/Standard VAS.docx", as_attachment=True)

# ✅ SMART OFFLINE CHATBOT (With broader understanding)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower().strip()

    expanded = {
        "ac storage": [
            "ac storage", "what is the rate for ac", "how much for ac unit", "rate of ac warehouse",
            "airconditioned storage", "ac type"
        ],
        "non-ac storage": [
            "non-ac storage", "non ac rate", "rate for non ac", "how much for non ac warehouse"
        ],
        "open shed": [
            "open shed", "shed rate", "shed storage price", "shed warehouse", "open shed cost"
        ],
        "chemical ac": [
            "chemical ac", "chemical airconditioned", "chem ac rate", "rate for chemical with ac"
        ],
        "chemical non-ac": [
            "chemical non-ac", "chemical non ac", "chem non ac", "rate for chemical non ac"
        ],
        "open yard mussafah": [
            "open yard mussafah", "yard in mussafah", "mussafah storage yard", "outside yard mussafah"
        ],
        "open yard kizad": [
            "open yard kizad", "yard in kizad", "kizad open space", "outside yard kizad"
        ],
        "wms": [
            "wms", "warehouse management", "system cost", "tracking system", "logistics system"
        ],
        "flatbed": [
            "flatbed", "flatbed truck", "truck with flat platform"
        ],
        "double trailer": [
            "double trailer", "two trailers", "long trailers"
        ],
        "small truck": [
            "small truck", "delivery truck", "van", "local truck"
        ],
        "forklift": [
            "forklift", "lift machine", "pallet lifter"
        ],
        "reachtruck": [
            "reachtruck", "reach truck", "high rack truck"
        ],
        "vna": [
            "vna", "very narrow aisle", "narrow aisle machine"
        ],
        "container 20": [
            "20 foot container", "20ft", "small container"
        ],
        "container 40": [
            "40 foot container", "40ft", "large container"
        ],
        "reefer": [
            "reefer", "refrigerated container", "cooling container"
        ],
        "who are you": [
            "who are you", "what is your name", "identify yourself"
        ],
        "hello": [
            "hi", "hello", "hey", "good morning", "good afternoon"
        ],
        "thank you": [
            "thanks", "thank you", "appreciate it"
        ],
        "what is dsv": [
            "what is dsv", "about dsv", "explain dsv"
        ],
        "dsv services": [
            "what does dsv offer", "dsv capabilities", "services by dsv", "dsv activities"
        ],
        "contact": [
            "how can i contact dsv", "dsv phone", "reach dsv", "contact details"
        ],
        "distance jebel ali to mussafah": [
            "distance between jebel ali and mussafah", "how far is jebel ali from mussafah"
        ],
        "distance jebel ali to abu dhabi": [
            "distance jebel ali to abu dhabi", "how far is abu dhabi from jebel ali"
        ],
        "distance dubai to sharjah": [
            "distance from dubai to sharjah", "how far is sharjah from dubai"
        ]
    }

    responses = {
        "ac storage": "AC storage is charged at 2.5 AED per CBM per day.",
        "non-ac storage": "Non-AC storage is 2.0 AED per CBM per day.",
        "open shed": "Open Shed storage is 1.8 AED per CBM per day.",
        "chemical ac": "Chemical AC storage is 3.5 AED per CBM per day.",
        "chemical non-ac": "Chemical Non-AC is 2.7 AED per CBM per day.",
        "open yard mussafah": "Open Yard in Mussafah is charged at 160 AED per SQM per year.",
        "open yard kizad": "Open Yard in KIZAD is charged at 125 AED per SQM per year.",
        "wms": "WMS is 1500 AED per month unless you're storing in Open Yard (then it’s excluded).",
        "flatbed": "Flatbed trucks are for palletized or container transport with a 12–14m bed.",
        "double trailer": "Double trailers are used for high-volume loads, mostly for inter-emirate transport.",
        "small truck": "Small trucks are for last-mile delivery and local distribution.",
        "forklift": "Forklifts handle pallets up to 3 tons inside warehouses or yards.",
        "reachtruck": "Reach trucks are used for narrow aisles, up to 11m high racking.",
        "vna": "VNA (Very Narrow Aisle) equipment is for high-density automated warehousing.",
        "container 20": "20ft containers are 6.1m long, up to 28,000kg cargo capacity.",
        "container 40": "40ft containers are 12.2m long, ideal for bulk or full container loads.",
        "reefer": "Reefer containers are refrigerated for perishables and sensitive cargo.",
        "who are you": "I'm DSV Assistant. Ask me anything about DSV logistics, storage, or transport.",
        "hello": "Hello! How can I support you today?",
        "thank you": "You're most welcome! 😊",
        "what is dsv": "DSV is a global transport and logistics company operating in 80+ countries.",
        "dsv services": "DSV offers warehousing, transport, customs clearance, air/sea/land freight, and supply chain solutions.",
        "contact": "You can contact DSV UAE via the website or call our offices in Mussafah or Jebel Ali.",
        "distance jebel ali to mussafah": "It’s approximately 125 km from Jebel Ali Port to Mussafah.",
        "distance jebel ali to abu dhabi": "The distance is about 140 km from Jebel Ali to Abu Dhabi.",
        "distance dubai to sharjah": "The distance from Dubai to Sharjah is around 30 km."
    }

    for tag, variants in expanded.items():
        for variant in variants:
            if variant in message:
                return jsonify({"reply": responses[tag]})

    return jsonify({
        "reply": "I'm sorry, I didn't understand that. Please ask about DSV storage, logistics, trucks, or transport."
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
