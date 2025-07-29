from flask import Flask, render_template, request, send_file, jsonify
from docx import Document
import os
import re
from datetime import datetime

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
    today_str = datetime.today().strftime("%d %b %Y")

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
        "{{TOTAL_FEE}}": f"{total_fee:,.2f} AED",
        "{{TODAY_DATE}}": today_str
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

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower().strip()

    def normalize(text):
        text = re.sub(r"\bu\b", "you", text)
        text = re.sub(r"\bur\b", "your", text)
        text = re.sub(r"\br\b", "are", text)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        return text

    message = normalize(message)

    def match(patterns):
        return any(re.search(p, message) for p in patterns)

    # --- Storage Rate Matching ---
    if match([r"open yard.*mussafah"]):
        return jsonify({"reply": "Open Yard Mussafah storage is 160 AED/SQM/year. WMS is excluded. VAS includes forklifts, cranes, and container lifts."})
    if match([r"open yard.*kizad"]):
        return jsonify({"reply": "Open Yard KIZAD storage is 125 AED/SQM/year. WMS excluded. VAS includes forklift 90–320 AED/hr, crane 250–450 AED/hr."})
    if match([r"ac storage|air conditioned"]):
        return jsonify({"reply": "AC storage is 2.5 AED/CBM/day. Standard VAS applies: 20 AED/CBM handling, 125 AED documentation, etc."})
    if match([r"non.?ac storage|non air"]):
        return jsonify({"reply": "Non-AC storage is 2.0 AED/CBM/day. Standard VAS applies."})
    if match([r"open shed"]):
        return jsonify({"reply": "Open Shed storage is 1.8 AED/CBM/day. Standard VAS applies: 12 AED/pallet, 85 AED for palletized packing."})
    if match([r"chemical ac"]):
        return jsonify({"reply": "Chemical AC storage is 3.5 AED/CBM/day. Chemical VAS applies: 20–25 AED/CBM handling, 150 AED docs."})
    if match([r"chemical non.?ac"]):
        return jsonify({"reply": "Chemical Non-AC storage is 2.7 AED/CBM/day. Chemical VAS applies."})

    # --- VAS Category Triggers ---
    if match([r"standard vas|normal vas|handling charges|pallet charges"]):
        return jsonify({"reply": "Standard VAS: 20 AED/CBM handling, 12 AED/pallet, 125 AED/documentation, 85 AED/CBM for palletized packing."})
    if match([r"chemical vas|hazmat vas"]):
        return jsonify({"reply": "Chemical VAS: 20–25 AED/CBM handling, 3.5 AED inner bags, 150 AED documentation, 85 AED/CBM pallet packing."})
    if match([r"open yard vas|forklift|crane|yard charges"]):
        return jsonify({"reply": "Open Yard VAS includes forklift (90–320 AED/hr), crane (250–450 AED/hr), and container lift (250 AED/lift)."})

    # --- Mussafah 21K Warehouse Info ---
    if match([r"21k|main warehouse|mussafah warehouse|dsv warehouse abu dhabi"]):
        return jsonify({"reply": "DSV’s 21K warehouse in Mussafah is 21,000 SQM, 15m clear height. Rack types: Selective (2.95–3.3m aisles), VNA (1.95m), Drive-in (2.0m)."})

    # --- Transport & Equipment ---
    if match([r"flatbed|double trailer|small truck|delivery truck"]):
        return jsonify({"reply": "DSV operates flatbeds, double trailers, and small city trucks for transport within UAE and GCC."})
    if match([r"forklift|reach truck|vna truck|warehouse equipment"]):
        return jsonify({"reply": "Forklifts (3T–15T), Reach trucks for 11m racks, VNA trucks for 1.95m aisles are available in DSV sites."})

    # --- Services & 3PL/4PL ---
    if match([r"\b3pl\b|third party logistics|order fulfillment"]):
        return jsonify({"reply": "DSV provides 3PL services: storage, inventory, picking, packing, labeling, delivery, returns."})
    if match([r"\b4pl\b|control tower|supply chain orchestrator"]):
        return jsonify({"reply": "As a 4PL provider, DSV coordinates multiple vendors to manage your end-to-end logistics strategy."})

    # --- Friendly Chat ---
    if match([r"\bhello\b|\bhi\b|\bhey\b|good morning|good evening"]):
        return jsonify({"reply": "Hello! I'm here to help with anything related to DSV logistics, transport, or warehousing."})
    if match([r"how.?are.?you|how.?s.?it.?going|whats.?up"]):
        return jsonify({"reply": "I'm doing great! How can I assist you with DSV services today?"})
    if match([r"\bthank(s| you)?\b|thx|appreciate"]):
        return jsonify({"reply": "You're very welcome! 😊"})

    # --- Fallback (never ask to rephrase) ---
    return jsonify({"reply": "I'm trained on everything related to DSV storage, transport, VAS, Mussafah warehouse, and services. Can you try asking again with more detail?"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
