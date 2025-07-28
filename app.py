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
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower().strip()

    def normalize(text):
        # Replace common shortcuts and typos
        text = re.sub(r"\bu\b", "you", text)
        text = re.sub(r"\bur\b", "your", text)
        text = re.sub(r"\br\b", "are", text)
        text = re.sub(r"\bpls\b|\bplz\b", "please", text)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        return text

    message = normalize(message)

    def match(patterns):
        return any(re.search(p, message) for p in patterns)

    # Redirect quotation-related messages
    if match([
        r"(give|send|share).*quote",
        r"(need|want|require|get).*quote",
        r"(need|want|require|get).*(quotation|proposal)",
        r"(how much|cost|price).*storage",
        r"generate.*quotation"
    ]):
        return jsonify({"reply": "Please close this chat and enter the storage type, volume, and duration in the Quotation Generator form to get an official proposal."})

    # Greetings & small talk
    if match([r"how.?are.?you", r"how.?s.?it.?going", r"what.?s.?up", r"bhow.?are.?u"]):
        return jsonify({"reply": "I'm doing well, thank you! How can I assist you with DSV services today?"})
    if match([r"\bhello\b", r"\bhi\b", r"\bhey\b", r"good morning", r"good afternoon", r"good evening"]):
        return jsonify({"reply": "Hello! I'm here to assist you with DSV logistics, warehousing, or transport inquiries."})
    if match([r"\bthank(s| you)\b", r"\bappreciate\b", r"thx"]):
        return jsonify({"reply": "You're most welcome! 😊"})

    # About DSV
    if match([r"\bwhat is dsv\b", r"\babout dsv\b", r"\bdsv overview\b", r"who.*dsv"]):
        return jsonify({"reply": "DSV is a global logistics leader founded in 1976 in Denmark. It offers transport and warehousing in over 90 countries and is listed on Nasdaq Copenhagen."})
    if match([r"dsv.*public", r"listed on", r"stock", r"shares"]):
        return jsonify({"reply": "Yes, DSV is publicly listed on Nasdaq Copenhagen and has a 100% free float — no majority shareholder."})
    if match([r"headquarters|hq|where.*based"]):
        return jsonify({"reply": "DSV is headquartered in Hedehusene, Denmark, and operates across 90+ countries with 160,000+ employees post-Schneker acquisition."})
    if match([r"divisions|structure|business model"]):
        return jsonify({"reply": "DSV is structured into Air & Sea (freight forwarding), Road (trucking), and Solutions (contract logistics including 3PL/4PL)."})

    if match([r"growth|acquisition|buy", r"(panalpina|uti|schenker|agility)"]):
        return jsonify({"reply": "DSV has grown through major acquisitions: UTi (2016), Panalpina (2019), Agility GIL (2021), and DB Schenker (2025), becoming the world's largest logistics provider."})

    if match([r"vision|mission|strategy"]):
        return jsonify({"reply": "DSV's vision is to be a top global logistics provider through scalable, sustainable growth and high customer satisfaction."})
    # Abu Dhabi & UAE details
    if match([r"abu dhabi", r"uae branch", r"mussafah", r"khalifa industrial", r"khia6", r"aeauh"]):
        return jsonify({"reply": "DSV Abu Dhabi has facilities in Mussafah (M-19), Khalifa Industrial Zone (KHIA6‑3_4), and Airport Freezone. Operating hours are Mon–Fri, 08:00–17:00."})
    if match([r"contact|phone|email|reach out|how.*call"]):
        return jsonify({"reply": "You can reach DSV Abu Dhabi at +971 2 509 9599 or AE.AUHSales@ae.dsv.com. Fax: +971 2 551 4833."})

    # Transport & logistics
    if match([r"air freight|sea freight|lcl|fcl|ocean"]):
        return jsonify({"reply": "DSV offers air freight (including charters) and sea freight (LCL, FCL, out-of-gauge, special cargo) with customs support."})
    if match([r"road transport|trucking|delivery|domestic|interstate"]):
        return jsonify({"reply": "DSV provides UAE-wide trucking, international road transport, project cargo handling, and subcontracted trailer combos."})
    if match([r"project cargo|oversize|nonstandard|heavy lift"]):
        return jsonify({"reply": "Yes, DSV handles project freight including oversized and non-standard items with cranes and special trailers."})
    if match([r"insurance|cargo insurance"]):
        return jsonify({"reply": "DSV offers cargo insurance options for road, air, and sea shipments upon request."})
    if match([r"customs|clearance|documentation|duties|tariff"]):
        return jsonify({"reply": "DSV provides end-to-end customs clearance, HS classification, duty optimization, and compliance advisory."})

    # Logistics Models
    if match([r"\b2pl\b|basic storage|handling only"]):
        return jsonify({"reply": "2PL includes basic storage, movement, and space rental—used in simple warehouse engagements."})
    if match([r"\b3pl\b|third party logistics|outsourcing"]):
        return jsonify({"reply": "3PL includes warehousing, inventory, order fulfillment, cross-docking, VAS like labeling and returns."})
    if match([r"\b4pl\b|control tower|end to end|orchestration"]):
        return jsonify({"reply": "DSV acts as a 4PL partner, coordinating multiple 3PLs and optimizing your entire supply chain."})

    # Specialized offerings
    if match([r"drone|inspection|delivery by drone"]):
        return jsonify({"reply": "DSV offers drone-based inspection for solar farms, pipelines, offshore sites, and light parcel delivery."})
    if match([r"ev truck|electric vehicle|zero emission"]):
        return jsonify({"reply": "Yes, DSV operates EV trucks capable of 40-ft double trailers (~30 tons), up to 250 km range, UAE-compliant."})
    if match([r"marine|barge|tug|supply vessel|dp vessel|offshore"]):
        return jsonify({"reply": "DSV provides marine charter services: tugboats, barges, supply and DP vessels, and crew accommodation—especially for Oil & Gas."})
    if match([r"reverse logistics|circular|repair|recycle|refurbish"]):
        return jsonify({"reply": "DSV supports circular-economy logistics—repair, refurbishment, returns, recycling and reverse fulfillment flows."})

    # VAS rates (Standard, Chemical, Open Yard)
    if match([r"chemical.*vas|hazmat handling|chem charges"]):
        return jsonify({"reply": "Chemical VAS: 20 AED/CBM in/out, 25 AED/CBM loose, 85 AED/CBM for packing with pallet, 3.5 AED for inner bags, and more."})
    if match([r"standard.*vas|normal vas|handling charges"]):
        return jsonify({"reply": "Standard VAS: 20 AED/CBM in/out, 12 AED/pallet, 125 AED/documentation, 2.5 AED for case picking, 85 AED/CBM packing with pallet."})
    if match([r"open yard.*vas|yard charges|forklift|crane"]):
        return jsonify({"reply": "Open Yard VAS: forklift 90–320 AED/hr (3T–15T), crane 250–450 AED/hr (50T–80T), container lift 250 AED/lift (20ft/40ft)."})

    # Fallback
    return jsonify({"reply": "I'm here to help with DSV’s global and Abu Dhabi logistics, warehousing, transport, or VAS services. Could you rephrase or specify your question?"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
