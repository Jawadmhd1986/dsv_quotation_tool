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
        
# --- Containers ---
    if match([r"20ft container|20 foot|twenty foot"]):
        return jsonify({"reply": "A 20ft container is 6.1m long, ~28,000 kg capacity, ideal for compact or heavy cargo."})
    if match([r"40ft container|40 foot|forty foot"]):
        return jsonify({"reply": "A 40ft container is 12.2m long, ~30,400 kg capacity. Ideal for bulk or palletized cargo."})
    if match([r"high cube|hc container|40ft high cube"]):
        return jsonify({"reply": "High Cube containers are 2.9m tall, 1 foot taller than standard. Ideal for bulky goods."})
    if match([r"reefer|refrigerated container|chiller container"]):
        return jsonify({"reply": "Reefer containers maintain temperatures for food, pharma, and perishables. Available in 20ft and 40ft."})
    if match([r"open top container|open roof|no roof container"]):
        return jsonify({"reply": "Open Top containers are used for tall cargo like machines, steel, or timber loaded by crane."})
    if match([r"flat rack|no sides container"]):
        return jsonify({"reply": "Flat Rack containers have no sides or roof, ideal for oversized cargo like vehicles or transformers."})

    # --- Pallet Info ---
    if match([r"pallet size|pallet dimension|standard pallet|euro pallet"]):
        return jsonify({"reply": "Standard pallet: 1.2m x 1.0m, Euro pallet: 1.2m x 0.8m. Standard = 14 per bay, Euro = 21 per bay in 21K."})

    # --- VAS Categories ---
    if match([r"standard vas|normal vas|handling charges|pallet charges|vas for ac|vas for non ac|vas for open shed"]):
        return jsonify({"reply": "Standard VAS includes:\n- In/Out Handling: 20 AED/CBM\n- Pallet Loading: 12 AED/pallet\n- Documentation: 125 AED/set\n- Packing with pallet: 85 AED/CBM\n- Inventory Count: 3,000 AED/event\n- Case Picking: 2.5 AED/carton\n- Sticker Labeling: 1.5 AED/label\n- Shrink Wrapping: 6 AED/pallet\n- VNA Usage: 2.5 AED/pallet"})

    if match([r"chemical vas|hazmat vas"]):
        return jsonify({"reply": "Chemical VAS includes:\n- Handling (Palletized): 20 AED/CBM\n- Handling (Loose): 25 AED/CBM\n- Documentation: 150 AED/set\n- Packing with pallet: 85 AED/CBM\n- Inventory Count: 3,000 AED/event\n- Inner Bag Picking: 3.5 AED/bag\n- Sticker Labeling: 1.5 AED/label\n- Shrink Wrapping: 6 AED/pallet"})

    if match([r"open yard vas|yard equipment|forklift rate|crane rate|container lifting|yard charges"]):
        return jsonify({"reply": "Open Yard VAS includes:\n- Forklift (3T–7T): 90 AED/hr\n- Forklift (10T): 200 AED/hr\n- Forklift (15T): 320 AED/hr\n- Mobile Crane (50T): 250 AED/hr\n- Mobile Crane (80T): 450 AED/hr\n- Container Lifting: 250 AED/lift\n- Container Stripping (20ft): 1,200 AED/hr"})

    # --- Chemical Quotation Required Docs ---
    if match([r"store.*chemical|quotation.*chemical|data.*chemical|requirement.*chemical"]):
        return jsonify({"reply": "To quote for chemical storage, we need:\n- Material name\n- Hazard class\n- CBM\n- Period\n- MSDS (Material Safety Data Sheet)."})

    # --- 21K Warehouse Rack System ---
    if match([r"rack height|rack levels|pallets per bay|rack system"]):
        return jsonify({"reply": "21K warehouse racks are 12m tall with 6 pallet levels. Each bay holds 14 Standard pallets or 21 Euro pallets."})

    # --- Storage Rate Synonym ---
    if match([r"ac storage rate|non ac rate|open shed rate|storage cost"]):
        return jsonify({"reply": "AC: 2.5 AED/CBM/day\nNon-AC: 2.0 AED/CBM/day\nOpen Shed: 1.8 AED/CBM/day. WMS is optional unless it's Open Yard."})
    # --- Chamber Mapping ---
    if match([r"ch2|chamber 2"]):
        return jsonify({"reply": "Chamber 2 is used by PSN (Federal Authority of Protocol and Strategic Narrative)."})
    if match([r"ch3|chamber 3"]):
        return jsonify({"reply": "Chamber 3 is used by food clients and fast-moving items."})
    if match([r"who.*in.*chamber|who.*in.*ch\d+"]):
        return jsonify({"reply": "The chambers in 21K warehouse are:\nCh1 – Khalifa University\nCh2 – PSN\nCh3 – Food clients\nCh4 – MCC, TR, ADNOC\nCh5 – PSN\nCh6 – ZARA, TR\nCh7 – Civil Defense & RMS"})

    # --- Warehouse Occupancy ---
    if match([r"warehouse occupancy|space available|any space in warehouse|availability.*storage"]):
        return jsonify({"reply": "For warehouse occupancy, contact Biju Krishnan at biju.krishnan@dsv.com."})
    if match([r"open yard.*occupancy|yard space.*available|yard capacity|yard.*availability"]):
        return jsonify({"reply": "For open yard occupancy, contact Antony Jeyaraj at antony.jeyaraj@dsv.com."})

    # --- EV trucks ---
    if match([r"ev truck|electric vehicle|zero emission|sustainable transport"]):
        return jsonify({"reply": "DSV Abu Dhabi operates EV trucks hauling 40ft containers. Each has ~250–300 km range and supports port shuttles & green logistics."})

    # --- DSV Managing Director (MD) ---
    if match([r"\bmd\b|managing director|head of dsv|boss of dsv|hossam mahmoud"]):
        return jsonify({"reply": "Mr. Hossam Mahmoud is the Managing Director of DSV Abu Dhabi. He oversees all logistics, warehousing, and transport operations in the region."})

    # --- What is WMS ---
    if match([r"what is wms|wms meaning|warehouse management system"]):
        return jsonify({"reply": "WMS stands for Warehouse Management System. DSV uses INFOR WMS for inventory control, inbound/outbound, and full visibility."})

    # --- What does DSV mean ---
    if match([r"what does dsv mean|dsv abbreviation|dsv stands for"]):
        return jsonify({"reply": "DSV originally stood for 'De Sammensluttede Vognmænd' in Danish, meaning 'The United Hauliers'. Today, DSV is a global brand."})

    # --- Industry Tags (FMCG, Insurance, Healthcare, Ecommerce) ---
    if match([r"\bfmcg\b|fast moving|consumer goods"]):
        return jsonify({"reply": "DSV provides fast turnaround warehousing for FMCG clients including dedicated racking, SKU control, and high-frequency dispatch."})
    if match([r"insurance|is insurance included|cargo insurance"]):
        return jsonify({"reply": "Insurance is not included by default in quotations. It can be arranged separately upon request."})
    if match([r"healthcare|medical storage|pharma warehouse|pharmaceutical storage"]):
        return jsonify({"reply": "DSV serves healthcare clients via temperature-controlled, GDP-compliant storage at Abu Dhabi Airport Freezone and Mussafah."})
    if match([r"ecommerce|online store|marketplace|e-commerce|order fulfillment"]):
        return jsonify({"reply": "DSV provides 3PL fulfillment for e-commerce clients including receiving, storage, picking, packing, returns, and delivery."})

    # --- Lean Six Sigma ---
    if match([r"lean six sigma|6 sigma|warehouse process improvement|lean method"]):
        return jsonify({"reply": "DSV incorporates Lean Six Sigma to improve warehouse efficiency, reduce errors, and optimize process flow with measurable KPIs."})

    # --- Warehouse Activities ---
    if match([r"warehouse activities|inbound process|outbound process|putaway|replenishment|picking|packing|cycle count"]):
        return jsonify({"reply": "Warehouse activities include:\n- Inbound: receiving, inspection, putaway\n- Outbound: picking, packing, dispatch\n- Replenishment, cycle counting, returns, VAS, and system updates via WMS."})

    # --- Machinery / Machineries ---
    if match([r"machinery|machineries|machines used|equipment used"]):
        return jsonify({"reply": "DSV uses forklifts (3–15T), VNA, reach trucks, pallet jacks, cranes, and container lifters in warehouse and yard operations."})
# --- Mussafah 21K Warehouse Info ---
    if match([r"21k.*rack height|rack height.*21k"]):
        return jsonify({"reply": "The racks in the 21K warehouse in Mussafah are 12 meters high, with 6 pallet levels plus ground. DSV uses both Euro and Standard pallets. Each bay holds up to 14 Standard pallets or 21 Euro pallets."})

    if match([r"pallet.*bay|how many.*bay.*pallet", r"bay.*standard pallet", r"bay.*euro pallet"]):
        return jsonify({"reply": "Each bay in 21K can accommodate 14 Standard pallets or 21 Euro pallets. This layout maximizes efficiency for various cargo sizes."})

    # --- DSV Ecommerce, Healthcare, Insurance, WMS ---
    if match([r"ecommerce|online store|fulfillment|dsv.*ecommerce"]):
        return jsonify({"reply": "DSV offers full e-commerce logistics: inbound, storage, pick & pack, same-day delivery, returns, and integrations with platforms like Shopify and Magento. Our KIZAD site supports high-volume order processing and Autostore automation."})

    if match([r"healthcare|pharma client|medical storage|health logistics"]):
        return jsonify({"reply": "DSV handles healthcare and pharmaceutical logistics with temperature-controlled storage, GDP compliance, and dedicated cold chain delivery. Our Airport Freezone warehouse is optimized for these sectors."})

    if match([r"insurance|cargo insurance|storage insurance|are items insured"]):
        return jsonify({"reply": "Insurance is not included by default in DSV storage or transport quotes. It can be arranged upon client request, and is subject to cargo value, category, and terms agreed."})

    if match([r"\bwms\b|warehouse management system|inventory software|tracking system|dsv.*system"]):
        return jsonify({"reply": "DSV uses the INFOR Warehouse Management System (WMS) to manage inventory, inbound/outbound flows, and order tracking. It supports real-time dashboards and client integration."})

    if match([r"what does dsv mean|dsv full form|dsv stands for"]):
        return jsonify({"reply": "DSV stands for 'De Sammensluttede Vognmænd' which means 'The Consolidated Hauliers' in Danish. It reflects DSV’s origin as a group of independent trucking companies in Denmark."})

    if match([r"warehouse activities|warehouse tasks|daily warehouse work"]):
        return jsonify({"reply": "DSV warehouse activities include receiving (inbound), put-away, storage, replenishment, order picking, packing, staging, and outbound dispatch. We also handle inventory audits, cycle counts, and VAS."})

    if match([r"warehouse process|inbound|outbound|putaway|replenishment|dispatch"]):
        return jsonify({"reply": "Typical warehouse processes at DSV: (1) Inbound receiving, (2) Put-away into racks or zones, (3) Order picking or replenishment, (4) Packing & labeling, (5) Outbound dispatch. All steps are WMS-tracked."})

    if match([r"lean six sigma|warehouse improvement|continuous improvement|kaizen|process efficiency"]):
        return jsonify({"reply": "DSV applies Lean Six Sigma principles in warehouse design and process flow to reduce waste, improve accuracy, and maximize efficiency. We implement 5S, KPI dashboards, and root-cause analysis for continuous improvement."})

    # --- Chemical Storage Quotation Requirement ---
    if match([r"quote.*chemical.*storage|store.*chemical.*quote|quotation.*chemical.*storage"]):
        return jsonify({"reply": "To provide a quotation for chemical storage, we require: 1) Product type, 2) Daily CBM/SQM, 3) MSDS (Material Safety Data Sheet), 4) Storage duration, 5) Special handling needs."})

    if match([r"\bmsds\b|material safety data sheet|chemical data"]):
        return jsonify({"reply": "Yes, MSDS (Material Safety Data Sheet) is mandatory for any chemical storage inquiry. It ensures safe handling and classification of the materials stored in DSV’s facilities."})

    # --- Client Name Queries ---
    if match([r"who is in ch(\d+)|client in ch(\d+)|ch\d+"]):
        ch_num = re.search(r"ch(\d+)", message)
        if ch_num:
            chamber = int(ch_num.group(1))
            clients = {
                1: "Khalifa University",
                2: "PSN",
                3: "Food clients & fast-moving items",
                4: "MCC, TR, and ADNOC",
                5: "PSN",
                6: "ZARA & TR",
                7: "Civil Defense and the RMS"
            }
            client_name = clients.get(chamber, "unknown")
            return jsonify({"reply": f"Chamber {chamber} is occupied by {client_name}."})
    
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
