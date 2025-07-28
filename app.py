from flask import Flask, render_template, request, send_file, jsonify
from docx import Document
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/generate", methods=["POST"])
def generate():
    storage_type = request.form["storage_type"]
    volume = float(request.form["volume"])
    days = int(request.form["days"])
    include_wms = request.form["wms"] == "Yes"
    email = request.form.get("email", "")

    # Select template
    if "chemical" in storage_type.lower():
        template_path = "templates/Chemical VAS.docx"
    elif "open yard" in storage_type.lower():
        template_path = "templates/Open Yard VAS.docx"
    else:
        template_path = "templates/Standard VAS.docx"

    doc = Document(template_path)

    # Rate logic
    if storage_type == "AC":
        rate = 2.5
        unit = "CBM"
        rate_unit = "CBM / DAY"
        storage_fee = volume * days * rate
    elif storage_type == "Non-AC":
        rate = 2.0
        unit = "CBM"
        rate_unit = "CBM / DAY"
        storage_fee = volume * days * rate
    elif storage_type == "Open Shed":
        rate = 1.8
        unit = "CBM"
        rate_unit = "CBM / DAY"
        storage_fee = volume * days * rate
    elif storage_type == "Chemicals AC":
        rate = 3.5
        unit = "CBM"
        rate_unit = "CBM / DAY"
        storage_fee = volume * days * rate
    elif storage_type == "Chemicals Non-AC":
        rate = 2.7
        unit = "CBM"
        rate_unit = "CBM / DAY"
        storage_fee = volume * days * rate
    elif "kizad" in storage_type.lower():
        rate = 125
        unit = "SQM"
        rate_unit = "SQM / YEAR"
        storage_fee = volume * days * (rate / 365)
    elif "mussafah" in storage_type.lower():
        rate = 160
        unit = "SQM"
        rate_unit = "SQM / YEAR"
        storage_fee = volume * days * (rate / 365)
    else:
        rate = 0
        storage_fee = 0
        unit = "CBM"
        rate_unit = "CBM / DAY"

    storage_fee = round(storage_fee, 2)
    months = max(1, days // 30)
    is_open_yard = "open yard" in storage_type.lower()
    wms_fee = 0 if is_open_yard or not include_wms else 1500 * months
    total_fee = round(storage_fee + wms_fee, 2)

    placeholders = {
        "{{STORAGE_TYPE}}": storage_type,
        "{{DAYS}}": str(days),
        "{{VOLUME}}": str(volume),
        "{{UNIT}}": unit,
        "{{WMS_STATUS}}": "" if is_open_yard else ("INCLUDED" if include_wms else "NOT INCLUDED"),
        "{{UNIT_RATE}}": f"{rate:.2f} AED / {rate_unit}",
        "{{STORAGE_FEE}}": f"{storage_fee:,.2f} AED",
        "{{WMS_FEE}}": f"{wms_fee:,.2f} AED",
        "{{TOTAL_FEE}}": f"{total_fee:,.2f} AED"
    }

    def replace_placeholders(doc, mapping):
        for p in doc.paragraphs:
            for key, val in mapping.items():
                if key in p.text:
                    p.text = p.text.replace(key, val)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for key, val in mapping.items():
                        if key in cell.text:
                            cell.text = cell.text.replace(key, val)

    replace_placeholders(doc, placeholders)

    def delete_block(doc, start_tag, end_tag):
        inside = False
        to_delete = []
        for i, p in enumerate(doc.paragraphs):
            if start_tag in p.text:
                inside = True
                to_delete.append(i)
            elif end_tag in p.text:
                to_delete.append(i)
                inside = False
            elif inside:
                to_delete.append(i)
        for i in reversed(to_delete):
            doc.paragraphs[i]._element.getparent().remove(doc.paragraphs[i]._element)

    if "open yard" in storage_type.lower():
        delete_block(doc, "[VAS_STANDARD]", "[/VAS_STANDARD]")
        delete_block(doc, "[VAS_CHEMICAL]", "[/VAS_CHEMICAL]")
    elif "chemical" in storage_type.lower():
        delete_block(doc, "[VAS_STANDARD]", "[/VAS_STANDARD]")
        delete_block(doc, "[VAS_OPENYARD]", "[/VAS_OPENYARD]")
    else:
        delete_block(doc, "[VAS_CHEMICAL]", "[/VAS_CHEMICAL]")
        delete_block(doc, "[VAS_OPENYARD]", "[/VAS_OPENYARD]")

    os.makedirs("generated", exist_ok=True)
    filename_prefix = email.split('@')[0] if email else "quotation"
    filename = f"Quotation_{filename_prefix}.docx"
    output_path = os.path.join("generated", filename)
    doc.save(output_path)

    return send_file(output_path, as_attachment=True)

# ✅ OFFLINE SMART CHATBOT LOGIC
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower().strip()

    synonyms = {
        "ac storage": ["ac", "air conditioned", "ac storage rate", "rate for ac"],
        "non-ac storage": ["non ac", "non-ac", "non ac rate"],
        "open shed": ["shed", "open shed rate"],
        "chemical ac": ["chemical ac", "chemical air conditioned", "chem ac"],
        "chemical non-ac": ["chemical non ac", "chem non ac"],
        "open yard mussafah": ["open yard mussafah", "mussafah yard"],
        "open yard kizad": ["open yard kizad", "kizad yard"],
        "wms": ["wms", "warehouse management", "system charge"],
        "flatbed": ["flatbed truck", "flatbed"],
        "double trailer": ["double trailer", "2 trailers"],
        "small truck": ["small truck", "delivery truck", "city truck"],
        "forklift": ["forklift", "fork lift"],
        "reachtruck": ["reachtruck", "reach truck"],
        "vna": ["vna", "very narrow aisle"],
        "container 20": ["20ft", "20 foot", "small container"],
        "container 40": ["40ft", "40 foot", "large container"],
        "reefer": ["reefer", "refrigerated container"],
        "who are you": ["who are you", "what is your name"],
        "hello": ["hello", "hi", "hey"],
        "thank you": ["thanks", "thank you", "appreciate it"],
        "what is dsv": ["what is dsv", "about dsv"],
        "dsv services": ["dsv services", "what does dsv offer"],
        "contact": ["contact", "how can i reach dsv"],
        "distance jebel ali to mussafah": ["jebel ali to mussafah"],
        "distance jebel ali to abu dhabi": ["jebel ali to abu dhabi"],
        "distance dubai to sharjah": ["dubai to sharjah"]
    }

    responses = {
        "ac storage": "AC storage is charged at 2.5 AED per CBM per day.",
        "non-ac storage": "Non-AC storage is 2.0 AED per CBM per day.",
        "open shed": "Open Shed storage is 1.8 AED per CBM per day.",
        "chemical ac": "Chemical AC storage is 3.5 AED per CBM per day.",
        "chemical non-ac": "Chemical Non-AC is 2.7 AED per CBM per day.",
        "open yard mussafah": "Open Yard in Mussafah is 160 AED per SQM per year.",
        "open yard kizad": "Open Yard in KIZAD is 125 AED per SQM per year.",
        "wms": "WMS is charged at 1500 AED per month, unless it's Open Yard (excluded).",
        "flatbed": "Flatbed trucks are used for pallets/containers with 12-14m beds.",
        "double trailer": "Double trailers transport large loads, usually between emirates or ports.",
        "small truck": "Small trucks are used for city deliveries and last-mile logistics.",
        "forklift": "Forklifts move pallets and lift up to 3 tons.",
        "reachtruck": "Reach trucks operate in narrow aisles, reaching 11 meters high.",
        "vna": "VNA (Very Narrow Aisle) trucks are used in automated warehouses with tight racking.",
        "container 20": "20ft containers are 6.1m long, carry 28,000kg, used for general cargo.",
        "container 40": "40ft containers are 12.2m long, for high-volume cargo up to 30,400kg.",
        "reefer": "Reefer containers are refrigerated for perishable goods.",
        "who are you": "I'm the DSV Assistant. Ask me anything about our logistics or warehousing.",
        "hello": "Hello! How can I assist you with DSV services?",
        "thank you": "You're very welcome! 😊",
        "what is dsv": "DSV is a global logistics company operating in over 80 countries.",
        "dsv services": "DSV offers warehousing, transport, customs clearance, and global freight solutions.",
        "contact": "You can reach DSV UAE via the official website or contact our Mussafah or Jebel Ali offices.",
        "distance jebel ali to mussafah": "Distance from Jebel Ali Port to Mussafah is approximately 125 km.",
        "distance jebel ali to abu dhabi": "Distance from Jebel Ali to Abu Dhabi is about 140 km.",
        "distance dubai to sharjah": "Distance from Dubai to Sharjah is around 30 km."
    }

    for tag, variants in synonyms.items():
        for variant in variants:
            if variant in message:
                return jsonify({"reply": responses[tag]})

    return jsonify({"reply": "I'm sorry, I didn't understand that. Please ask about DSV storage, logistics, trucks, or transport."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
