from flask import Flask, render_template, request, send_file, jsonify
from docx import Document
import os
import re

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

# ✅ SMART OFFLINE CHATBOT
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower().strip()

    def match(patterns):
        return any(re.search(p, message) for p in patterns)

    if match([
        r"(give|send|share).*quote",
        r"(i )?(need|want).*(quotation|proposal)",
        r"(how much|cost|price).*storage",
        r"generate.*quotation"
    ]):
        return jsonify({"reply": "Please close this chat and enter the storage type, volume, and duration in the Quotation Generator form to get an official proposal."})

    if match([r"\bhow are you\b", r"\bhow's it going\b", r"\bwhat's up\b"]):
        return jsonify({"reply": "I'm doing well, thank you! How can I assist you with DSV services today?"})
    if match([r"\bhello\b", r"\bhi\b", r"\bhey\b"]):
        return jsonify({"reply": "Hello! I'm here to help you with DSV logistics, warehousing, or transport inquiries."})
    if match([r"\bthank(s| you)\b", r"\bappreciate\b"]):
        return jsonify({"reply": "You're most welcome! 😊"})

    if match([r"\bwhat is dsv\b", r"\babout dsv\b", r"\bdsv overview\b"]):
        return jsonify({"reply": "DSV is a global logistics and transport company operating in over 80 countries, offering services in air, sea, road freight, and contract logistics."})
    if match([r"\bdsv abu dhabi\b", r"\bdsv uae\b", r"where is dsv located"]):
        return jsonify({"reply": "DSV Solutions PJSC is located in Mussafah Industrial Area, Abu Dhabi. The warehouse includes AC, non-AC, open shed, and open yard storage zones."})
    if match([r"warehouse size", r"how big.*warehouse", r"capacity.*warehouse"]):
        return jsonify({"reply": "DSV Abu Dhabi facility includes over 25,000+ SQM of covered space and 40,000+ SQM open yard capacity."})

    if match([r"\b3pl\b", r"third party logistics"]):
        return jsonify({"reply": "3PL (Third-Party Logistics) refers to outsourcing logistics operations like warehousing, transport, and distribution to companies like DSV."})
    if match([r"\b4pl\b", r"fourth party logistics"]):
        return jsonify({"reply": "4PL (Fourth-Party Logistics) involves managing and integrating multiple supply chain providers — DSV can act as a 4PL for large enterprises."})

    if match([r"\bac storage\b", r"air ?conditioned", r"ac warehouse"]):
        return jsonify({"reply": "AC storage is 2.5 AED per CBM per day."})
    if match([r"\bnon[- ]?ac\b", r"non air", r"non ac storage"]):
        return jsonify({"reply": "Non-AC storage is 2.0 AED per CBM per day."})
    if match([r"open shed"]):
        return jsonify({"reply": "Open Shed storage is 1.8 AED per CBM per day."})
    if match([r"chemical.*ac"]):
        return jsonify({"reply": "Chemical AC storage is 3.5 AED per CBM per day."})
    if match([r"chemical.*non.*ac"]):
        return jsonify({"reply": "Chemical Non-AC storage is 2.7 AED per CBM per day."})
    if match([r"open yard.*kizad"]):
        return jsonify({"reply": "Open Yard in KIZAD is 125 AED per SQM per year."})
    if match([r"open yard.*mussafah"]):
        return jsonify({"reply": "Open Yard in Mussafah is 160 AED per SQM per year."})

    if match([r"\bwms\b", r"warehouse management", r"system charge"]):
        return jsonify({"reply": "WMS (Warehouse Management System) is 1500 AED/month unless excluded for Open Yard."})

    if match([r"\bvas\b", r"value added", r"handling charges", r"loading", r"offloading", r"pallet", r"carton", r"documentation"]):
        if "chemical" in message:
            return jsonify({"reply": "Chemical VAS includes 20 AED/CBM for handling palletized, 25 AED/CBM for loose, 85 AED/CBM for packing with wooden pallet, etc."})
        elif "open yard" in message:
            return jsonify({"reply": "Open Yard VAS includes forklift (90–320 AED/hr), cranes (250–450 AED/hr), and container lifting from 250 AED/lift."})
        else:
            return jsonify({"reply": "Standard VAS includes 20 AED/CBM for handling, 12 AED/pallet, 125 AED/document, and more."})

    if match([r"forklift", r"reach ?truck", r"\bvna\b", r"very narrow aisle", r"crane", r"equipment", r"machinery"]):
        return jsonify({"reply": "Available equipment includes forklifts (3T–15T), reach trucks, VNAs, and cranes (50T–80T) for all types of cargo handling."})

    if match([r"flatbed", r"double trailer", r"small truck", r"transport", r"fleet", r"truck types"]):
        return jsonify({"reply": "DSV operates flatbed trucks, double trailers, and city trucks for UAE-wide deliveries and port movements."})

    if match([r"20ft", r"20.*container"]):
        return jsonify({"reply": "20ft container: 6.1m, 28,000kg capacity, used for standard cargo."})
    if match([r"40ft", r"40.*container"]):
        return jsonify({"reply": "40ft container: 12.2m, 30,400kg capacity, ideal for large volume loads."})
    if match([r"reefer", r"refrigerated container"]):
        return jsonify({"reply": "Reefer containers are temperature-controlled, used for food and pharmaceuticals."})

    if match([r"jebel ali.*mussafah"]):
        return jsonify({"reply": "Distance from Jebel Ali Port to Mussafah is around 125 km."})
    if match([r"jebel ali.*abu dhabi"]):
        return jsonify({"reply": "Distance from Jebel Ali to Abu Dhabi is approximately 140 km."})
    if match([r"dubai.*sharjah"]):
        return jsonify({"reply": "Distance from Dubai to Sharjah is approximately 30 km."})

    return jsonify({"reply": "I'm here to help with DSV’s logistics, transport, warehouse, and storage info. Could you rephrase or ask a specific question?"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
