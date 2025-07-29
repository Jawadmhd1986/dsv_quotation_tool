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

# FRIENDLY CHAT BLOCK SHOULD BE HERE
    if match([r"\bhello\b|\bhi\b|\bhey\b|good morning|good evening"]):
        return jsonify({"reply": "Hello! I'm here to help with anything related to DSV logistics, transport, or warehousing."})
    if match([r"how.?are.?you|how.?s.?it.?going|whats.?up"]):
        return jsonify({"reply": "I'm doing great! How can I assist you with DSV services today?"})
    if match([r"\bthank(s| you)?\b|thx|appreciate"]):
        return jsonify({"reply": "You're very welcome! 😊"})

# --- Handling Math Questions like Packing Calculations ---
    if match([r"calculate.*packing.*pallet", r"how much.*pallet.*packing", r"cost.*packing.*pallet", r"packing with pallet for \d+ pallet"]):
        match_pallets = re.search(r"(\d+)\s*pallet", message)
        if match_pallets:
            pallets = int(match_pallets.group(1))
            rate = 85
            total = pallets * rate
            return jsonify({"reply": f"Packing with pallet for {pallets} pallets at 85 AED/CBM each = {total:,.2f} AED."})
                # --- VAS Calculation: Detect quantity and item type ---
    if match([r"calculate.*(handling|in.?out)", r"how much.*handling", r"cost.*handling.*cbm"]):
        cbm_match = re.search(r"(\d+)\s*cbm", message)
        if cbm_match:
            cbm = int(cbm_match.group(1))
            rate = 20
            return jsonify({"reply": f"In/Out Handling for {cbm} CBM at 20 AED/CBM = {cbm * rate:,.2f} AED."})

    if match([r"calculate.*pallet.*load", r"pallet.*loading.*\d+", r"loading.*unloading.*pallet"]):
        pallet_match = re.search(r"(\d+)\s*pallet", message)
        if pallet_match:
            pallets = int(pallet_match.group(1))
            return jsonify({"reply": f"Pallet loading/unloading for {pallets} pallets at 12 AED/pallet = {pallets * 12:,.2f} AED."})

    if match([r"calculate.*documentation|doc charge|docs.*rate|how much.*doc"]):
        sets_match = re.search(r"(\d+)\s*(sets|doc)", message)
        sets = int(sets_match.group(1)) if sets_match else 1
        return jsonify({"reply": f"Documentation for {sets} set(s) at 125 AED/set = {sets * 125:,.2f} AED."})

    if match([r"calculate.*packing.*pallet", r"pallet.*packing.*\d+", r"how much.*packing"]):
        pallet_match = re.search(r"(\d+)\s*pallet", message)
        if pallet_match:
            pallets = int(pallet_match.group(1))
            return jsonify({"reply": f"Packing with pallet for {pallets} pallets at 85 AED/CBM = {pallets * 85:,.2f} AED."})

    if match([r"inventory count", r"stock audit", r"inventory event", r"inventory.*charge"]):
        return jsonify({"reply": "Inventory Count fee is 3,000 AED per event."})

    if match([r"case picking.*\d+", r"carton.*picking", r"how much.*carton"]):
        carton_match = re.search(r"(\d+)\s*carton", message)
        if carton_match:
            cartons = int(carton_match.group(1))
            return jsonify({"reply": f"Case picking for {cartons} cartons at 2.5 AED/carton = {cartons * 2.5:,.2f} AED."})

    if match([r"label.*sticker.*\d+", r"sticker.*label.*cost", r"label.*qty"]):
        label_match = re.search(r"(\d+)\s*label", message)
        if label_match:
            labels = int(label_match.group(1))
            return jsonify({"reply": f"Sticker labeling for {labels} labels at 1.5 AED/label = {labels * 1.5:,.2f} AED."})

    if match([r"shrink wrap.*\d+", r"wrap.*pallet", r"how much.*wrap"]):
        wrap_match = re.search(r"(\d+)\s*pallet", message)
        if wrap_match:
            pallets = int(wrap_match.group(1))
            return jsonify({"reply": f"Shrink wrapping for {pallets} pallets at 6 AED/pallet = {pallets * 6:,.2f} AED."})

    if match([r"vna usage.*\d+", r"very narrow aisle.*pallet", r"vna.*charge"]):
        pallet_match = re.search(r"(\d+)\s*pallet", message)
        if pallet_match:
            pallets = int(pallet_match.group(1))
            return jsonify({"reply": f"VNA usage for {pallets} pallets at 2.5 AED/pallet = {pallets * 2.5:,.2f} AED."})
                # --- Chemical VAS Calculation ---
    if match([r"chemical.*handling.*pallet|palletized.*chemical", r"handling.*chemical.*pallet"]):
        cbm_match = re.search(r"(\d+)\s*cbm", message)
        if cbm_match:
            cbm = int(cbm_match.group(1))
            return jsonify({"reply": f"Chemical handling (palletized) for {cbm} CBM at 20 AED/CBM = {cbm * 20:,.2f} AED."})

    if match([r"chemical.*handling.*loose|loose.*chemical", r"handling.*chemical.*loose"]):
        cbm_match = re.search(r"(\d+)\s*cbm", message)
        if cbm_match:
            cbm = int(cbm_match.group(1))
            return jsonify({"reply": f"Chemical handling (loose) for {cbm} CBM at 25 AED/CBM = {cbm * 25:,.2f} AED."})

    if match([r"chemical.*doc|chemical.*documentation|chemical.*paperwork"]):
        sets_match = re.search(r"(\d+)\s*(sets|doc)", message)
        sets = int(sets_match.group(1)) if sets_match else 1
        return jsonify({"reply": f"Chemical documentation for {sets} set(s) at 150 AED/set = {sets * 150:,.2f} AED."})

    if match([r"chemical.*packing.*pallet|chemical.*palletized", r"packing.*chemical.*cbm"]):
        cbm_match = re.search(r"(\d+)\s*cbm", message)
        if cbm_match:
            cbm = int(cbm_match.group(1))
            return jsonify({"reply": f"Chemical packing with pallet for {cbm} CBM at 85 AED/CBM = {cbm * 85:,.2f} AED."})

    if match([r"chemical.*inventory|chemical.*stock|chemical.*audit"]):
        return jsonify({"reply": "Chemical inventory count is charged at 3,000 AED per event."})

    if match([r"chemical.*inner bag|inner bag picking|bag picking|bag.*pick.*\d+"]):
        bag_match = re.search(r"(\d+)\s*bag", message)
        if bag_match:
            bags = int(bag_match.group(1))
            return jsonify({"reply": f"Inner bag picking for {bags} bags at 3.5 AED/bag = {bags * 3.5:,.2f} AED."})

    if match([r"chemical.*label|chemical.*sticker.*label|labeling.*chemical"]):
        label_match = re.search(r"(\d+)\s*label", message)
        if label_match:
            labels = int(label_match.group(1))
            return jsonify({"reply": f"Chemical sticker labeling for {labels} labels at 1.5 AED/label = {labels * 1.5:,.2f} AED."})

    if match([r"chemical.*wrap|shrink wrap.*chemical|chemical.*shrink"]):
        pallet_match = re.search(r"(\d+)\s*pallet", message)
        if pallet_match:
            pallets = int(pallet_match.group(1))
            return jsonify({"reply": f"Chemical shrink wrapping for {pallets} pallets at 6 AED/pallet = {pallets * 6:,.2f} AED."})
                # --- Open Yard VAS Calculation ---
    if match([r"forklift.*3.*7|3t.*forklift|7t.*forklift"]):
        hr_match = re.search(r"(\d+)\s*hour", message)
        if hr_match:
            hrs = int(hr_match.group(1))
            return jsonify({"reply": f"Forklift (3T–7T) for {hrs} hour(s) at 90 AED/hr = {hrs * 90:,.2f} AED."})

    if match([r"forklift.*10t|10t.*forklift"]):
        hr_match = re.search(r"(\d+)\s*hour", message)
        if hr_match:
            hrs = int(hr_match.group(1))
            return jsonify({"reply": f"Forklift (10T) for {hrs} hour(s) at 200 AED/hr = {hrs * 200:,.2f} AED."})

    if match([r"forklift.*15t|15t.*forklift"]):
        hr_match = re.search(r"(\d+)\s*hour", message)
        if hr_match:
            hrs = int(hr_match.group(1))
            return jsonify({"reply": f"Forklift (15T) for {hrs} hour(s) at 320 AED/hr = {hrs * 320:,.2f} AED."})

    if match([r"crane.*50t|50t.*crane|mobile crane.*50"]):
        hr_match = re.search(r"(\d+)\s*hour", message)
        if hr_match:
            hrs = int(hr_match.group(1))
            return jsonify({"reply": f"Mobile Crane (50T) for {hrs} hour(s) at 250 AED/hr = {hrs * 250:,.2f} AED."})

    if match([r"crane.*80t|80t.*crane|mobile crane.*80"]):
        hr_match = re.search(r"(\d+)\s*hour", message)
        if hr_match:
            hrs = int(hr_match.group(1))
            return jsonify({"reply": f"Mobile Crane (80T) for {hrs} hour(s) at 450 AED/hr = {hrs * 450:,.2f} AED."})

    if match([r"container.*lift|container lifting|lift.*container|20ft.*lift|40ft.*lift"]):
        unit_match = re.search(r"(\d+)\s*(lift|container)", message)
        lifts = int(unit_match.group(1)) if unit_match else 1
        return jsonify({"reply": f"{lifts} container lift(s) at 250 AED/lift = {lifts * 250:,.2f} AED."})

    if match([r"container.*strip|stripping.*20ft|20ft.*strip|strip.*container"]):
        hr_match = re.search(r"(\d+)\s*hour", message)
        if hr_match:
            hrs = int(hr_match.group(1))
            return jsonify({"reply": f"Container Stripping 20ft for {hrs} hour(s) at 1,200 AED/hr = {hrs * 1200:,.2f} AED."})



    # --- Storage Rate Matching ---
    if match([r"open yard.*mussafah"]):
        return jsonify({"reply": "Open Yard Mussafah storage is 160 AED/SQM/year. WMS is excluded. VAS includes forklifts, cranes, and container lifts."})
    if match([r"open yard.*kizad"]):
        return jsonify({"reply": "Open Yard KIZAD storage is 125 AED/SQM/year. WMS excluded. VAS includes forklift 90–320 AED/hr, crane 250–450 AED/hr."})
        # --- Specific Chamber Questions ---
    if match([r"who is in chamber 2|chamber 2.*client|client in chamber 2"]):
        return jsonify({"reply": "Chamber 2 in the 21K warehouse is allocated to PSN (Federal Authority of Protocol and Strategic Narrative)."})

    # --- MD recognition for abbreviation ---
    if match([r"\bmd\b", r"who is the md", r"managing director", r"head of dsv abu dhabi"]):
        return jsonify({"reply": "Mr. Hossam Mahmoud is the Managing Director of DSV Abu Dhabi."})

    # --- 'what does DSV do' ---
    if match([r"what.*dsv.*do", r"dsv.*services", r"what is dsv.*business", r"what.*offer.*dsv"]):
        return jsonify({"reply": "DSV offers global logistics services including Air & Sea freight, Road transport, warehousing, 3PL/4PL solutions, and value-added services. In Abu Dhabi, we specialize in industrial, oil & gas, FMCG, healthcare, and government logistics."})
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
    # --- UAE Transportation Distance Responses ---
    if match([r"abu dhabi.*dubai|dubai.*abu dhabi"]):
        return jsonify({"reply": "The distance between Abu Dhabi and Dubai is approximately 140 km by road."})
        # --- Chemical Storage Quotation Requirements ---
    if match([
    r"(what|which).*data.*(chemical|hazmat).*quote",
    r"(chemical|hazmat).*quotation.*need.*(info|details|data)",
    r"if i.*store.*chemical.*what.*you need",
    r"chemical.*storage.*quotation.*requirement",
    r"(quotation|quote).*for.*chemicals.*what.*needed"]):
        return jsonify({"reply": (
        "To provide a quotation for chemical storage, we need:\n"
        "- Material Safety Data Sheet (MSDS)\n"
        "- Type and classification of chemical (e.g. flammable, corrosive)\n"
        "- Required volume in CBM\n"
        "- Duration of storage (in days or months)\n"
        "- Packaging type (palletized or loose)\n"
        "- Any special handling or temperature requirements\n"
        "- Delivery/pickup expectations or transport support\n"
        "Once we have these details, we can prepare a tailored quotation with appropriate VAS.")})

    if match([r"abu dhabi.*sharjah|sharjah.*abu dhabi"]):
        return jsonify({"reply": "The distance between Abu Dhabi and Sharjah is about 160 km."})
    if match([r"abu dhabi.*ajman|ajman.*abu dhabi"]):
        return jsonify({"reply": "The distance between Abu Dhabi and Ajman is approximately 170 km."})
    if match([r"abu dhabi.*ras al khaimah|rak.*abu dhabi"]):
        return jsonify({"reply": "The road distance from Abu Dhabi to Ras Al Khaimah is about 240 km."})
    if match([r"abu dhabi.*fujairah|fujairah.*abu dhabi"]):
        return jsonify({"reply": "Abu Dhabi to Fujairah is approximately 250 km by road."})
    if match([r"dubai.*sharjah|sharjah.*dubai"]):
        return jsonify({"reply": "Dubai to Sharjah is just around 30 km — very close and commonly traveled."})
    if match([r"dubai.*ajman|ajman.*dubai"]):
        return jsonify({"reply": "Dubai to Ajman is approximately 40 km by road."})
    if match([r"dubai.*rak|ras al khaimah.*dubai"]):
        return jsonify({"reply": "The distance between Dubai and Ras Al Khaimah is around 120 km."})
    if match([r"dubai.*fujairah|fujairah.*dubai"]):
        return jsonify({"reply": "Dubai to Fujairah is approximately 130 km."})
    if match([r"sharjah.*ajman|ajman.*sharjah"]):
        return jsonify({"reply": "Sharjah and Ajman are extremely close — only about 15 km apart."})
    if match([r"sharjah.*fujairah|fujairah.*sharjah"]):
        return jsonify({"reply": "Sharjah to Fujairah is roughly 110 km."})
    if match([r"sharjah.*rak|ras al khaimah.*sharjah"]):
        return jsonify({"reply": "Sharjah to Ras Al Khaimah is approximately 100 km."})
    # --- DSV Temperature-Controlled Storage Zones ---
    if match([r"temperature controlled|climate control|ambient temp|controlled storage|18.*25"]):
        return jsonify({"reply": "DSV's temperature-controlled zones are maintained between +18°C to +25°C — ideal for dry food, electronics, and general goods that require stable ambient conditions."})
    # --- Insurance Coverage Inquiry ---
    if match([r"insurance|is insurance included|cargo insurance|do you provide insurance|insurance coverage|quotation insurance|shipment insurance"]):
        return jsonify({"reply": "Insurance is not included by default in DSV quotations. If required, it can be arranged upon client request and will be quoted separately. Please mention this need when requesting your quotation or proposal."})
    if match([r"\bmsds\b", r"chemical.*quote.*data", r"quotation.*chemical.*info", r"what.*needed.*chemical.*quote"]):
        return jsonify({"reply": "To receive a quotation for chemical storage, please provide: (1) Material type, (2) Volume in CBM, (3) Duration, (4) Storage conditions, and (5) MSDS (Material Safety Data Sheet)."})

    if match([r"\bwarehouse.*activity|warehouse process|inbound|outbound|replenishment|cycle count|inventory control"]):
        return jsonify({"reply": "DSV warehouse activities include inbound receiving, storage, replenishment, outbound order fulfillment, inventory cycle counting, labeling, palletization, and dispatch with WMS tracking."})

    if match([r"lean six sigma|6 sigma|lean method|process improvement"]):
        return jsonify({"reply": "DSV applies Lean Six Sigma principles to eliminate waste, streamline logistics workflows, and improve accuracy and efficiency in warehouse and transport operations."})

    if match([r"\bfmcg\b|fast moving consumer goods|dsv fmcg"]):
        return jsonify({"reply": "DSV supports FMCG clients with temperature-controlled storage, rapid picking, labeling, VAS, and distribution. Our systems ensure fast throughput for high-volume SKU handling."})

    if match([r"\bheathcare\b|\bhealthcare\b|medical supply|pharmaceutical|dsv healthcare"]):
        return jsonify({"reply": "DSV serves the healthcare sector with cold chain logistics, secure pharma storage, GDP-compliant processes, and custom handling for vaccines, medical devices, and hospital inventory."})

    if match([r"wms|warehouse management system|what system.*dsv|dsv.*system|name of system"]):
        return jsonify({"reply": "DSV uses the INFOR Warehouse Management System (WMS) across our UAE operations for inventory control, live visibility, task management, and data integration."})

    if match([r"ecommerce|online retail|web order|last mile delivery|online shipment|fulfillment center"]):
        return jsonify({"reply": "DSV offers eCommerce support with same-day/next-day fulfillment, pick & pack, labeling, returns management, and last-mile delivery — supported by automated WMS systems and live tracking."})

    if match([r"ch ?2|chamber 2|who.*chamber 2"]):
        return jsonify({"reply": "Chamber 2 in DSV's 21K warehouse is allocated to PSN (Federal Authority of Protocol and Strategic Narrative)."})

    if match([r"ch ?3|chamber 3|who.*chamber 3"]):
        return jsonify({"reply": "Chamber 3 in 21K houses food clients and fast-moving items, optimized for high turnover."})

    if match([r"ch ?4|chamber 4|who.*chamber 4"]):
        return jsonify({"reply": "Chamber 4 stores inventory for MCC, TR, and ADNOC clients with dedicated access."})

    if match([r"who is maher|maher abu alhaija"]):
        return jsonify({"reply": "Maher Abu AlHaija is a senior DSV team member involved in warehouse and operations leadership in Abu Dhabi."})

    if match([r"how many.*pallet.*bay|standard.*bay.*pallet|euro.*bay.*pallet"]):
        return jsonify({"reply": "Each bay in DSV’s 21K warehouse can hold up to 14 Standard pallets or 21 Euro pallets. Racks are 12m high and allow for 6 pallet levels."})

    if match([r"vas.*ac storage"]):
        return jsonify({"reply": "AC Storage is 2.5 AED/CBM/day. Standard VAS includes:\n- Handling: 20 AED/CBM\n- Pallet: 12 AED\n- Documentation: 125 AED\n- Packing: 85 AED/CBM\n- Inventory: 3000 AED/event\n- Case Picking: 2.5 AED/carton\n- Labeling: 1.5 AED\n- Shrink Wrap: 6 AED\n- VNA: 2.5 AED/pallet"})

    if match([r"calculate.*packing.*pallet.*(\d+)"]):
        qty = int(re.search(r"(\d+)", message).group(1))
        cost = qty * 85
        return jsonify({"reply": f"Packing with pallet for {qty} pallets costs {cost:.2f} AED (at 85 AED/pallet)."})

    if match([r"calculate.*handling.*cbm.*(\d+)"]):
        cbm = int(re.search(r"(\d+)", message).group(1))
        cost = cbm * 20
        return jsonify({"reply": f"In/Out Handling for {cbm} CBM is {cost:.2f} AED (20 AED/CBM)."})

    if match([r"warehouse.*occupancy|do.*space.*warehouse|warehouse full|storage availability"]):
        return jsonify({"reply": "For warehouse occupancy inquiries, please contact Biju Krishnan at biju.krishnan@dsv.com."})

    if match([r"machinery|machineries|equipment storage|machine relocation"]):
        return jsonify({"reply": "DSV handles full relocation and storage for machinery, lab equipment, industrial tools, and high-value assets with packing, crating, and transportation included."})

    if match([r"what.*dsv.*do|dsv services|dsv offer|dsv support"]):
        return jsonify({"reply": "DSV provides global logistics, warehousing, 2PL/3PL/4PL, temperature-controlled storage, marine transport, relocation, e-commerce support, and heavy lift project cargo handling."})

    if match([r"\bmd\b|who is md|managing director"]):
        return jsonify({"reply": "The Managing Director of DSV Abu Dhabi is Mr. Hossam Mahmoud."})

    return jsonify({"reply": "I'm trained on everything related to DSV logistics, warehousing, storage types, VAS, projects, and transport. Can you please rephrase or specify your topic?"})
    # --- DSV Healthcare & Pharma Logistics ---
    if match([r"healthcare|pharma|pharmaceutical|medical storage|health logistics|cold chain|hospital delivery"]):
        return jsonify({"reply": "DSV provides healthcare and pharmaceutical logistics through cold chain storage (+2°C to +8°C), ambient storage (+18°C to +25°C), and deep freezer options (–22°C). We support inventory management, batch tracking, cold room compliance, and last-mile delivery to clinics, pharmacies, and hospitals. Healthcare clients are supported in Airport Freezone and KIZAD facilities."})
# --- DSV E-commerce Logistics ---
    if match([r"ecommerce|e-commerce|online retail|ecom|dsv online|shop logistics|online order|fulfillment center"]):
        return jsonify({"reply": "DSV provides end-to-end e-commerce logistics including warehousing, order fulfillment, pick & pack, returns handling, last-mile delivery, and integration with Shopify, Magento, and custom APIs. Our Autostore and WMS systems enable fast, accurate processing of online orders from our UAE hubs including KIZAD and Airport Freezone."})
# --- DSV Machinery Handling & Relocation ---
    if match([r"machinery|machines|equipment move|machine relocation|heavy machine|industrial equipment|machinery storage|dsv machineries"]):
        return jsonify({"reply": "DSV specializes in handling, relocating, and storing machinery and industrial equipment. We offer secure storage, packing, dismantling, loading, transport (including lowbeds and cranes), and reinstallation. Machinery logistics are handled under strict QHSE protocols using specialized staff and equipment."})

    if match([r"cold room|cold storage|chilled|2.*8 degree|refrigerated warehouse"]):
        return jsonify({"reply": "Our cold room zones are kept between +2°C and +8°C — perfect for medicines, vaccines, and fresh food items that require refrigeration."})

    if match([r"freezer|deep freeze|minus 22|negative storage|frozen room|below zero"]):
        return jsonify({"reply": "We offer deep freezer rooms set at –22°C for frozen goods like food, pharmaceuticals, and sensitive biotech products."})
    # --- QHSE & Warehouse Safety Training ---
    if match([r"qhse|hse|health and safety|quality control|warehouse safety|safety policy|safety audit"]):
        return jsonify({"reply": "DSV warehouses follow strict QHSE protocols including ISO-certified processes, ADNOC HSE standards, regular audits, PPE enforcement, and safety drills. We uphold a zero-incident culture and ensure compliance with all local and client-specific safety standards."})
    if match([r"how many.*ton.*truck|truck.*capacity|truck load.*kg|truck weight.*carry"]):
        return jsonify({"reply": (
        "Here’s the typical tonnage each DSV truck type can carry:\n"
        "- **Flatbed Truck**: up to 22–25 tons (ideal for general cargo, pallets, containers)\n"
        "- **Double Trailer (Articulated)**: up to 50–60 tons combined (used for long-haul or inter-emirate)\n"
        "- **Box Truck / Curtainside**: ~5–10 tons (weather-protected for packaged goods)\n"
        "- **Refrigerated Truck (Reefer)**: 3–12 tons depending on size (temperature-sensitive goods)\n"
        "- **City Truck (1–3 Ton)**: 1 to 3 tons (last-mile delivery within cities)\n"
        "- **Lowbed Trailer**: up to 60 tons for heavy equipment and machinery\n"
        "- **Tipper / Dump Truck**: ~15–20 tons of bulk material (sand, gravel, etc.)")})
    if match([r"(distance|how far|km).*mussafah.*(al markaz|markaz|hameem|hamim|ghayathi|ruwais|mirfa|madinat zayed|western region)"]):
        return jsonify({"reply": (
        "Approximate road distances from Mussafah:\n"
        "- Al Markaz: **60 km**\n"
        "- Hameem: **90 km**\n"
        "- Madinat Zayed: **150 km**\n"
        "- Mirfa: **140 km**\n"
        "- Ghayathi: **240 km**\n"
        "- Ruwais: **250 km**\n"
        "\nLet me know if you need travel time or transport support too.")})

    if match([r"safety training|warehouse training|fire drill|manual handling|staff safety|employee training|toolbox talk"]):
        return jsonify({"reply": "DSV staff undergo regular training in fire safety, first aid, manual handling, emergency response, and site induction. We also conduct toolbox talks and refresher sessions to maintain safety awareness and operational excellence."})
    # --- DSV & ADNOC Relationship ---
    if match([r"adnoc|adnoc project|dsv.*adnoc|oil and gas project|dsv support.*adnoc|logistics for adnoc"]):
        return jsonify({"reply": "DSV has an active relationship with ADNOC and its group companies, supporting logistics for Oil & Gas projects across Abu Dhabi. This includes warehousing of chemicals, fleet transport to remote sites, 3PL for EPC contractors, and marine logistics for ADNOC ISLP and offshore projects. All operations are QHSE compliant and meet ADNOC’s safety and performance standards."})
    # --- UAE Summer Midday Break ---
    if match([r"summer break|midday break|working hours summer|12.*3.*break|uae heat ban|no work afternoon|hot season schedule"]):
        return jsonify({"reply": "DSV complies with UAE summer working hour restrictions. From June 15 to September 15, all outdoor work (including open yard and transport loading) is paused daily between 12:30 PM and 3:30 PM. This ensures staff safety and follows MOHRE guidelines."})
    # --- DSV Abu Dhabi Facility Sizes ---
    if match([
        r"plot size", r"abu dhabi total area", r"site size", r"facility size", r"total sqm", r"how big",
        r"yard size", r"open yard area", r"size of open yard", r"open yard.*size", r"area of open yard"]):
        return jsonify({"reply": "DSV Abu Dhabi's open yard spans 360,000 SQM across Mussafah and KIZAD. The total logistics plot is 481,000 SQM, including 100,000 SQM of service roads and utilities, and a 21,000 SQM warehouse (21K)."})

    if match([r"sub warehouse|m44|m45|al markaz|abu dhabi warehouse total|all warehouses"]):
        return jsonify({"reply": "In addition to the main 21K warehouse, DSV operates sub-warehouses in Abu Dhabi: M44 (5,760 sqm), M45 (5,000 sqm), and Al Markaz (12,000 sqm). Combined with 21K, the total covered warehouse area in Abu Dhabi is approximately 44,000 sqm."})

    if match([r"terms and conditions|quotation policy|billing cycle|operation timing|payment terms|quotation validity"]):
        return jsonify({"reply": "DSV quotations include the following terms: Monthly billing, final settlement before vacating, 15-day quotation validity, subject to space availability. The depot operates Monday–Friday 8:30 AM to 5:30 PM. Insurance is not included by default. An environmental fee of 0.15% is added to all invoices. Non-moving cargo over 3 months may incur extra storage tariff."})
    if match([r"standard vas|normal vas|handling charges|pallet charges|vas for ac storage|vas for non ac|vas for open shed"]):
        return jsonify({"reply": "Standard VAS includes:\n- In/Out Handling: 20 AED/CBM\n- Pallet Loading/Unloading: 12 AED/pallet\n- Documentation: 125 AED per set\n- Packing with pallet: 85 AED/CBM\n- Inventory Count: 3,000 AED/event\n- Case Picking: 2.5 AED/carton\n- Sticker Labeling: 1.5 AED/label\n- Shrink Wrapping: 6 AED/pallet\n- VNA Usage: 2.5 AED/pallet"})

    if match([r"chemical vas|hazmat vas|vas for chemical ac|vas for chemical non ac"]):
        return jsonify({"reply": "Chemical VAS includes:\n- Handling (Palletized): 20 AED/CBM\n- Handling (Loose): 25 AED/CBM\n- Documentation: 150 AED per set\n- Packing with pallet: 85 AED/CBM\n- Inventory Count: 3,000 AED/event\n- Inner Bag Picking: 3.5 AED/bag\n- Sticker Labeling: 1.5 AED/label\n- Shrink Wrapping: 6 AED/pallet"})

    if match([r"open yard vas|yard charges|vas for open yard"]):
        return jsonify({"reply": "Open Yard VAS includes:\n- Forklift (3T–7T): 90 AED/hr\n- Forklift (10T): 200 AED/hr\n- Forklift (15T): 320 AED/hr\n- Mobile Crane (50T): 250 AED/hr\n- Mobile Crane (80T): 450 AED/hr\n- Container Lifting (20ft & 40ft): 250 AED/lift\n- Container Stripping 20ft: 1,200 AED/hr"})
# --- DSV Meaning / Full Form ---
    if match([r"\bwhat does dsv mean\b", r"\bmeaning of dsv\b", r"dsv full form", r"what is dsv", r"expand dsv", r"who.*dsv", r"dsv stands for"]):
        return jsonify({"reply": "DSV stands for 'De Sammensluttede Vognmænd' in Danish, which means 'The United Hauliers'. It was founded in 1976 in Denmark and has grown into a global logistics and transport company."})
# --- FMCG Explanation ---
    if match([r"\bfmcg\b", r"fast moving consumer goods", r"fmcg logistics", r"fmcg meaning", r"what is fmcg", r"fmcg storage", r"fmcg warehouse"]):
        return jsonify({"reply": "FMCG stands for Fast Moving Consumer Goods — products that sell quickly at relatively low cost such as food, beverages, toiletries, and over-the-counter drugs. DSV provides warehousing, order fulfillment, and last-mile delivery for FMCG clients, including temperature-controlled and ambient storage options."})
# --- WMS (Warehouse Management System) ---
    if match([r"\bwms\b", r"warehouse management system", r"what is wms", r"how does wms work", r"dsv wms", r"wms software"]):
        return jsonify({"reply": "WMS stands for Warehouse Management System. It's the software DSV uses to track inventory, manage warehouse operations, ensure order accuracy, and provide real-time visibility. DSV’s WMS integrates with client ERPs and supports barcode scanning, inventory alerts, and KPI reporting."})
# --- DSV Core System: INFOR ---
    if match([r"name of the system", r"system used in dsv", r"dsv system name", r"what erp", r"main software", r"which platform", r"dsv infor"]):
        return jsonify({"reply": "DSV uses INFOR as its core system for warehouse and logistics management. INFOR integrates with WMS, TMS, and client ERPs to streamline operations, provide real-time tracking, and support advanced reporting and automation."})
# --- 21K Warehouse Rack Height and Pallet Configuration ---
    if match([r"rack height|pallet levels|pallet per bay|rack capacity|rack storage|how many pallet|rack dimension|rack configuration|rack structure|racks info|rack design"]):
        return jsonify({"reply": "The 21K warehouse in Mussafah has racks with a height of 12 meters, accommodating 6 pallet levels above the ground. We use both Euro pallets and Standard pallets. Each bay can store 14 Standard pallets or 21 Euro pallets, optimized for high-density racking."})
# --- General Container Types Inquiry ---
    if match([r"\bcontainer\b|containers|types of containers|container info|shipping containers|container options|container sizes|cargo container|container used"]):
        return jsonify({"reply": "DSV provides multiple container types: 20ft (6.1m, ~28 tons), 40ft (12.2m, ~30.4 tons), 40ft High Cube (extra height), Reefers (temperature-controlled), Open Top (for oversized cargo), and Flat Racks (no sides/roof for machinery or bulky freight)."})

    # --- DSV Staffing Overview ---
    if match([r"how many staff|number of employees|team size|manpower|dsv people|dsv workers|dsv staff|uae staff|abu dhabi team"]):
        return jsonify({"reply": "DSV employs approximately 160,000 staff globally across 90+ countries. In the UAE, we have around 1,200 employees covering transport, warehousing, and freight. In Abu Dhabi, DSV operates with about 400 personnel across 21K, KIZAD, Airport Freezone, and administrative support teams."})
        # --- Mussafah to Specific Western Region Destinations ---
    if match([r"mussafah.*(al markaz|markaz)"]):
        return jsonify({"reply": "The distance from Mussafah to Al Markaz is approximately **60 km**, and it takes around **45–50 minutes** by road."})

    if match([r"mussafah.*hameem|mussafah.*hamim"]):
        return jsonify({"reply": "The distance from Mussafah to Hameem is approximately **90 km**, with a travel time of around **1 hour** by road."})

    if match([r"mussafah.*madinat zayed"]):
        return jsonify({"reply": "Mussafah to Madinat Zayed is about **150 km**, typically **1 hour 45 minutes** drive depending on traffic."})

    if match([r"mussafah.*mirfa"]):
        return jsonify({"reply": "The distance from Mussafah to Mirfa is approximately **140 km**, and the drive usually takes **1 hour 40 minutes**."})

    if match([r"mussafah.*ghayathi"]):
        return jsonify({"reply": "Mussafah to Ghayathi is around **240 km**, taking about **2 hours 45 minutes** by road."})

    if match([r"mussafah.*ruwais"]):
        return jsonify({"reply": "The distance from Mussafah to Ruwais is approximately **250 km**, and it takes around **3 hours** to reach by road."})
# --- Abu Dhabi ⇄ Other Emirates (Distance + Travel Time Both Directions) ---
    if match([r"(abu dhabi.*dubai|dubai.*abu dhabi)"]):
        return jsonify({"reply": "Abu Dhabi ⇄ Dubai: **140 km**, approx. **1 hour 30 minutes** by road."})

    if match([r"(abu dhabi.*sharjah|sharjah.*abu dhabi)"]):
        return jsonify({"reply": "Abu Dhabi ⇄ Sharjah: **160 km**, around **1 hour 45 minutes** travel time."})

    if match([r"(abu dhabi.*ajman|ajman.*abu dhabi)"]):
        return jsonify({"reply": "Abu Dhabi ⇄ Ajman: **170 km**, approx. **1 hour 50 minutes** by car."})

    if match([r"(abu dhabi.*ras al khaimah|rak.*abu dhabi|ras al khaimah.*abu dhabi)"]):
        return jsonify({"reply": "Abu Dhabi ⇄ Ras Al Khaimah: **240 km**, approx. **2 hours 45 minutes** by road."})

    if match([r"(abu dhabi.*fujairah|fujairah.*abu dhabi)"]):
        return jsonify({"reply": "Abu Dhabi ⇄ Fujairah: **250 km**, travel time is around **2 hours 50 minutes**."})

    if match([r"(abu dhabi.*umm al quwain|umm al quwain.*abu dhabi|uaq.*abu dhabi)"]):
        return jsonify({"reply": "Abu Dhabi ⇄ Umm Al Quwain: **190 km**, approx. **2 hours** by road."})

    if match([r"(abu dhabi.*al ain|al ain.*abu dhabi)"]):
        return jsonify({"reply": "Abu Dhabi ⇄ Al Ain: **170 km**, travel time is about **1 hour 45 minutes**."})

    # --- DSV Heavy Lift Projects & Capabilities ---
    if match([r"heavy lift|heavy cargo|over dimensional|odc|lowbed project|heavy logistics|crane transport|multi axle|project cargo"]):
        return jsonify({"reply": "DSV provides heavy lift and project logistics for over-dimensional and high-weight cargo. We use lowbed trailers, cranes, and multi-axle units. DSV has completed major projects for ADNOC and industrial clients — including transformer moves, skid-mounted modules, and heavy equipment delivery up to 100+ tons."})
    # --- 21K Warehouse Chambers Breakdown ---
    if match([r"chambers|warehouse sections|how many chambers|storage zones|warehouse division|client chambers|rooms in warehouse"]):
        return jsonify({"reply": "The 21K warehouse in Mussafah contains 7 chambers: Chamber 1 – Khalifa University; Chamber 2 – PSN; Chamber 3 – Food clients & fast-moving items; Chamber 4 – MCC, TR, and ADNOC; Chamber 5 – PSN; Chamber 6 – ZARA & TR; Chamber 7 – Civil Defense and the RMS (Record Management System). Each chamber is segregated for dedicated client needs and service flow."})
    # --- VVIP Clients Overview ---
    if match([r"vvip clients|important clients|key accounts|premium customers|special clients|top clients|confidential clients"]):
        return jsonify({"reply": "DSV works with several VVIP clients including ADNOC, PSN (Federal Authority of Protocol and Strategic Narrative), Civil Defense, Khalifa University, ZARA, and strategic EPCs. These clients are managed with strict SLAs, confidentiality protocols, and customized logistics — including private chambers, secured document storage, and dedicated transport services."})
    # --- DSV Technology: Autostore & Digital Onboarding ---
    if match([r"autostore|automation|robotics|automated warehouse|high density storage|robot picking|warehouse robots"]):
        return jsonify({"reply": "DSV offers Autostore technology — a robotic cube storage system that enables high-density storage and fast picking. It is ideal for e-commerce, small parts, and fast-moving SKUs, with minimal floor space and maximum efficiency."})
    if match([r"almarkaz|al markaz|markaz warehouse|almarkaz warehouse|sub warehouse.*markaz"]):
        return jsonify({"reply": "DSV operates a sub-warehouse in Al Markaz, Abu Dhabi, with a total covered area of 12,000 sqm. It supports general storage, 3PL activities, and overflow for large-scale industrial clients. Al Markaz complements our main 21K and M44/M45 sites."})
    # --- DSV Fleet Overview ---
    if match([r"\bfleet\b", r"dsv fleet", r"transport fleet", r"vehicle fleet", r"what trucks do you have", r"fleet types", r"truck options", r"transport equipment"]):
        return jsonify({"reply": "DSV operates a diverse transport fleet in the UAE, including flatbeds, double trailers, box trucks, refrigerated trucks (reefers), city vans (1–3 ton), lowbeds, tippers, and electric trucks. Our fleet supports last-mile, inter-emirate, heavy cargo, and temperature-controlled deliveries."})
    # --- Open Yard General Overview ---
    if match([r"\bopen yard\b", r"open yard area", r"yard facility", r"yard operations", r"what is open yard", r"yard logistics"]):
        return jsonify({"reply": "DSV’s open yard facilities in Abu Dhabi span over 360,000 SQM across Mussafah and KIZAD. These areas support container storage, heavy equipment, project cargo, and vehicle storage. We provide forklift, crane, and container lifting services. Rates range from 125–160 AED/SQM/year depending on location."})
    if match([r"sustainabil(ity|ty)", r"green logistics", r"carbon footprint", r"environment vision", r"eco friendly", r"zero emission", r"climate goal", r"green strategy", r"environmental policy"]):
        return jsonify({"reply": "DSV’s global sustainability vision focuses on reducing carbon emissions, introducing electric vehicles, enabling circular logistics (reuse, returns, refurbishment), and optimizing infrastructure for energy efficiency. DSV also helps clients reduce Scope 3 emissions and align with global sustainability goals."})
    # --- General Transportation Overview ---
    if match([r"\btransportation\b", r"\btransport\b", r"transport services", r"delivery service", r"how do you transport", r"moving cargo", r"freight services", r"logistics transport", r"road transport"]):
        return jsonify({"reply": "DSV provides comprehensive transportation services across the UAE and GCC. We operate flatbeds, double trailers, box trucks, reefers, city vans, lowbeds, tippers, and EV trucks. Services include last-mile delivery, project cargo, temperature-controlled freight, and cross-border trucking — all managed with real-time tracking and a strong operations control center (OCC)."})
    # --- General Technology Inquiry ---
    if match([r"\btechnology\b", r"digital system", r"tech platform", r"innovation", r"smart warehouse", r"dsv tech", r"digital solution", r"automated system"]):
        return jsonify({"reply": "DSV leverages advanced technology to support logistics and warehousing operations. This includes robotic Autostore systems, digital onboarding apps tailored to each client's process, RFID tracking, ERP integrations, and live dashboards for full visibility and control across transport and storage activities."})
    # --- General Equipment Inquiry ---
    if match([r"\bequipment\b", r"warehouse equipment", r"tools", r"machinery", r"what equipment do you use", r"material handling", r"forklift info", r"reach truck info"]):
        return jsonify({"reply": "DSV uses a full range of equipment across its facilities including forklifts (3T–15T), reach trucks for 11m high racks, VNA (Very Narrow Aisle) trucks for 1.95m aisles, manual pallet jacks, and mobile cranes for yard operations. All equipment is safety-certified and maintained under strict QHSE protocols."})
    if match([r"(transport availability|truck availability|trailer availability|flatbed available|can you deliver|book a truck|need a truck|truck timing)"]):
        return jsonify({"reply": "For any transportation needs or vehicle availability, kindly reach out to Ronnell Toring at ronnell.toring@dsv.com (DSV OCC team)."})
    # --- Packing Material Consumption Details ---
    if match([
    r"shrink wrap usage", r"stretch film per pallet", r"how many rolls", r"wrap quantity",
    r"packing capacity", r"strapping details", r"buckle usage",
    r"how many pallet.*(stretch|shrink|wrap|film)",
    r"(stretch|shrink|wrap).*how many pallet",
    r"(how many|usage).*shrink wrap", r"(how many|usage).*stretch film",
    r"(how many|usage).*strapping roll", r"(how many|usage).*strap buckle"]):
        return jsonify({"reply": "Each box of shrink/stretch film contains 6 rolls. Each roll can wrap up to 20 pallets (1.5m height). Each strapping roll secures 20 pallets. A box of strap buckles contains 1,000 pieces and supports up to 250 pallets. These materials are used by DSV for secure packing in relocation and warehouse operations."})
    # --- DSV Abu Dhabi Managing Director ---
    if match([
    r"hossam", r"hossam mahmoud", r"who is hossam", r"abu dhabi md", r"managing director",
    r"who leads abu dhabi", r"dsv uae head", r"head of dsv abu dhabi", r"boss of dsv"]):
        return jsonify({"reply": "Mr. Hossam Mahmoud is the Managing Director of DSV Abu Dhabi. With over 20 years of experience in regional logistics and supply chain management, he has led major operations for industrial, oil & gas, and government clients. Under his leadership, DSV expanded its footprint across Mussafah, KIZAD, and Airport Freezone, introducing advanced 4PL, EV trucking, and marine logistics services."})
    # --- DSV KIZAD Site Info ---
    if match([
    r"\bkizad\b", r"khalifa industrial", r"khalifa zone", r"khalifa port area",
    r"warehouse in kizad", r"dsv kizad site", r"dsv in kizad", r"abu dhabi kizad"]):
        return jsonify({"reply": "DSV operates a major facility in KIZAD (Khalifa Industrial Zone, Abu Dhabi) known as KHIA6‑3_4. It supports 3PL/4PL warehousing, industrial logistics, and cross-docking. This site complements our Mussafah 21K and Airport Freezone operations and is strategically positioned for port access and long-term projects."})
    if match([r"rms|record management system|document storage|file archive|document center|records store|rms 21k"]):
        return jsonify({"reply": "DSV’s 21K warehouse in Mussafah includes an RMS (Record Management System) facility for secure storage of client documentation. It features barcode indexing, controlled access, and retrieval tracking. The fire suppression system inside the RMS uses FM200 (clean agent gas) instead of water, ensuring sensitive records and paper files are protected from damage during emergencies."})
    if match([r"technology platform|onboarding apps|client system|customized app|erp|integration|application onboarding|digital process"]):
        return jsonify({"reply": "DSV tailors onboarding platforms and digital workflows to match each client's operations. Whether it's B2B bulk shipment, retail, or API-driven e-commerce, we integrate with ERPs, offer KPI dashboards, and deploy mobile RF systems for full visibility and control."})
    # --- RFID Solutions: Tracking, Gates, Asset Management ---
    if match([r"rfid|asset tracking|track items|inventory automation|rfid gate|tool management|scan tags|live tracking"]):
        return jsonify({"reply": "DSV provides advanced RFID solutions including fixed RFID gates at entry/exit points, handheld readers for bulk scans, and asset tracking systems. These are used for tool management, returnable packaging, and high-value item tracking — all integrated into client-specific dashboards for real-time visibility and control."})
    # --- Open Yard Occupancy Contact ---
    if match([r"open yard.*occupancy|yard availability|yard space|yard capacity|open yard full|yard rental|yard booking"]):
        return jsonify({"reply": "For open yard occupancy inquiries, please contact Antony Jeyaraj at antony.jeyaraj@dsv.com."})
    # --- Electric Vehicle (EV) Trucks ---
    if match([r"ev truck|electric vehicle|zero emission truck|sustainable transport|electric trailer|green logistics"]):
        return jsonify({"reply": "DSV Abu Dhabi operates electric trucks capable of hauling 40ft containers, including double-trailer combinations. These EV units have a range of up to 250–300 km per charge and are used for port shuttles, inter-emirate transport, and emission-free delivery — supporting DSV’s green logistics strategy."})
    # --- DSV Sustainability & Green Logistics ---
    if match([r"sustainability|green logistics|carbon footprint|environment vision|eco friendly|zero emission|climate goal|green strategy"]):
        return jsonify({"reply": "DSV’s global sustainability vision focuses on reducing carbon emissions, introducing electric vehicles, enabling circular logistics (reuse, returns, refurbishment), and optimizing infrastructure for energy efficiency. DSV also helps clients reduce Scope 3 emissions and align with global sustainability goals."})
    # --- Pallet Types and Dimensions ---
    if match([r"pallet size|pallet type|standard pallet|euro pallet|wooden pallet|plastic pallet|chemical pallet|cp pallet|pallet dimension"]):
        return jsonify({"reply": "DSV uses standard wooden pallets (1.2m x 1.0m), plastic pallets for food/pharma, and CP pallets for chemicals. Load capacity ranges up to 1,200 kg. Custom oversized pallets are also used for special cargo like machinery or large crates."})
    # --- DSV Relocation Services & Packing Materials ---
    if match([r"relocation|moving service|shifting|pack and move|relocate|office move|machine relocation|furniture relocation"]):
        return jsonify({"reply": "DSV’s relocation division handles full scope moves: offices, furniture, machinery, labs, and sensitive equipment. We provide professional packing, dismantling, loading, transport, and reassembly — across UAE and beyond."})

    if match([r"packing material|what material do you use for packing|box type|relocation packing|bubble wrap|carton box|wood crate"]):
        return jsonify({"reply": "DSV uses professional packing materials including double-ply cartons, bubble wrap, stretch film, blankets, corrugated sheets, and custom wooden crates for machines. All materials are industry-approved for safe relocation."})
    # --- Formula 1 Logistics Scope ---
    if match([r"formula 1|f1 logistics|grand prix|race logistics|f1 cargo|f1 shipping|yas marina|motorsport logistics"]):
        return jsonify({"reply": "Every year, DSV manages logistics for the Formula 1 Grand Prix — including air, sea, and road transport of race cars, pit equipment, team gear, and hospitality setups. We support the Abu Dhabi Grand Prix at Yas Marina with timed deliveries, customs handling, and re-export services."})
    # --- Packing Material Consumption Details ---
    if match([r"shrink wrap usage|stretch film per pallet|how many rolls|packing capacity|strapping details|buckle usage|wrap quantity"]):
        return jsonify({"reply": "Each box of shrink/stretch film contains 6 rolls. Each roll can wrap up to 20 pallets (1.5m height). Each strapping roll secures 20 pallets. A box of strap buckles contains 1,000 pieces and supports up to 250 pallets. These materials are used by DSV for secure packing in relocation and warehouse operations."})
    # --- Housekeeping and Security ---
    if match([r"housekeeping|cleanliness|cleaning staff|hygiene standard|warehouse cleaning|facility maintenance"]):
        return jsonify({"reply": "DSV maintains strict housekeeping standards across all facilities. We have dedicated teams for daily cleaning, pest control, waste segregation, and aisle organization. All practices follow ISO standards for hygiene and operational safety."})

    if match([r"security|guards|gates|entry check|warehouse security|chamber access|cctv|surveillance|gate control"]):
        return jsonify({"reply": "DSV facilities are protected by 24/7 manned security gates, warehouse access control, and CCTV monitoring. Security guards are stationed at all entry points and inside chambers for sensitive client areas. Access is controlled and logged in line with client confidentiality and HSE standards."})
    # --- Certifications & Access Control ---
    if match([r"gdsp certified|certifications|certified facility|warehouse standard|compliance|facility certification"]):
        return jsonify({"reply": "Yes, all DSV UAE facilities, including our Mussafah 21K warehouse, are GDSP certified — ensuring compliance with global safety, documentation, and operational protocols."})

    if match([r"access control|entry control|badge access|security system|who can enter|restricted area"]):
        return jsonify({"reply": "Access to DSV warehouses and chambers is controlled via secure gate systems and badge-based access control. Only authorized personnel can enter storage zones or sensitive areas such as VVIP chambers or RMS."})

    # --- VAS Category Triggers ---
    if match([r"standard vas|normal vas|handling charges|pallet charges"]):
        return jsonify({"reply": "Standard VAS: 20 AED/CBM handling, 12 AED/pallet, 125 AED/documentation, 85 AED/CBM for palletized packing."})
    if match([r"chemical vas|hazmat vas"]):
        return jsonify({"reply": "Chemical VAS: 20–25 AED/CBM handling, 3.5 AED inner bags, 150 AED documentation, 85 AED/CBM pallet packing."})
    if match([r"open yard vas|forklift|crane|yard charges"]):
        return jsonify({"reply": "Open Yard VAS includes forklift (90–320 AED/hr), crane (250–450 AED/hr), and container lift (250 AED/lift)."})
    # --- Container Types ---
    if match([r"20ft container|20 foot|small container|twenty foot"]):
        return jsonify({"reply": "A 20ft container is 6.1m long, holds ~28,000 kg of cargo, and is used for general shipping. It's ideal for compact or heavy loads."})
    if match([r"40ft container|40 foot|forty foot|large container"]):
        return jsonify({"reply": "A 40ft container is 12.2m long, holds up to ~30,400 kg. Commonly used for high-volume goods like furniture, textiles, and pallets."})
    if match([r"high cube|40ft high cube|hc container"]):
        return jsonify({"reply": "40ft High Cube containers are 1 foot taller than standard 40ft units (2.9m high). Used for tall or lightweight bulky cargo."})
    if match([r"reefer|refrigerated container|chiller|cold storage"]):
        return jsonify({"reply": "Reefer containers maintain temperature for perishable goods like food or pharmaceuticals. Available in 20ft and 40ft sizes."})
    if match([r"open top container|open roof|no roof container"]):
        return jsonify({"reply": "Open Top containers are used for cargo that exceeds normal height or needs crane loading — like machinery, timber, or scrap metal."})
    if match([r"flat rack|no sides container|machinery transport"]):
        return jsonify({"reply": "Flat Racks have no sides or roof. Ideal for oversized loads: vehicles, generators, industrial equipment, etc."})
    # --- Truck Types & Specifications ---
    if match([r"flatbed|flat bed truck|open trailer"]):
        return jsonify({"reply": "Flatbed trucks have no sides or roof and are ideal for pallets, containers, machinery, or timber. Typical size: 12–14m length, 2.5m width. Easy access for cranes or forklifts."})

    if match([r"double trailer|articulated truck|2 trailers|twin trailer"]):
        return jsonify({"reply": "Double-trailer trucks consist of two linked 40ft trailers (or equivalent volume), used for inter-emirate or GCC transport. Total length: ~25–28 meters. Payload: up to 60 tons combined."})

    if match([r"curtain side|box truck|enclosed truck|side loader|covered truck"]):
        return jsonify({"reply": "Curtainside or box trucks are enclosed for dust/weather protection. Common dimensions: 7–10m length, 2.5m width. Used for general cargo, retail, palletized goods."})

    if match([r"refrigerated truck|reefer truck|chiller|cold delivery|fridge truck"]):
        return jsonify({"reply": "Refrigerated trucks (reefers) maintain cargo temperatures from -20°C to +25°C. Available in 1–3 ton small trucks and 40ft trailers. Used for perishables, pharma, frozen food."})

    if match([r"small truck|city truck|van delivery|1 ton truck|last mile"]):
        return jsonify({"reply": "City delivery trucks are compact (3–5m length), typically 1–3 ton capacity. Perfect for last-mile drops inside Abu Dhabi, Dubai, or Sharjah."})

    if match([r"lowbed|low bed trailer|highbed|project cargo trailer"]):
        return jsonify({"reply": "Lowbed trailers are used for transporting construction machinery, transformers, and other heavy/oversized items. Deck height: ~0.8–1.0m. Load height clearance: up to 3.8m."})

    if match([r"tipper|dump truck|bulk material truck|gravel truck|sand truck"]):
        return jsonify({"reply": "Tippers (dump trucks) transport loose materials like sand, gravel, or debris. Typical capacity: 12–20 CBM. Feature rear or side hydraulic tipping."})
    # --- DSV Abu Dhabi Managing Director ---
    if match([r"abu dhabi md|managing director|who leads abu dhabi|dsv uae head|hossam mahmoud"]):
        return jsonify({"reply": "Mr. Hossam Mahmoud is the Managing Director of DSV Abu Dhabi. With over 20 years of experience in regional logistics and supply chain management, he has led major operations for industrial, oil & gas, and government clients. Under his leadership, DSV expanded its footprint across Mussafah, KIZAD, and Airport Freezone, introducing advanced 4PL, EV trucking, and marine logistics services."})
    # --- 2PL, 3PL, 4PL Services & UAE Use Cases ---
    if match([r"\b2pl\b|second party logistics|space rental|basic logistics"]):
        return jsonify({"reply": "2PL (Second-Party Logistics) at DSV includes basic storage and transportation. Clients typically lease warehouse space and manage their own inventory. In UAE, DSV offers 2PL to industrial suppliers storing long-term equipment in Mussafah."})

    if match([r"\b3pl\b|third party logistics|inventory management|value added service"]):
        return jsonify({"reply": "3PL (Third-Party Logistics) involves full operational outsourcing: storage, order processing, inventory, kitting, labeling, and delivery. DSV provides 3PL to e-commerce clients in KIZAD and healthcare distributors in Abu Dhabi Airport Freezone."})
    if match([r"formula ?1|f1|f 1|grand prix|yas marina|race logistics|motorsport"]):
        return jsonify({"reply": "Every year, DSV manages logistics for the Formula 1 Grand Prix — including air, sea, and road transport of race cars, pit equipment, team gear, and hospitality setups. We support the Abu Dhabi Grand Prix at Yas Marina with timed deliveries, customs handling, and re-export services."})

    # --- DSV ABU DHABI OVERVIEW ---
    if match([r"mussafah|abu dhabi|uae.*branch|dsv facilities|dsv warehouse|dsv mussafah|dsv kizad|dsv airport site|where is 21k"]):
        return jsonify({"reply": "DSV Abu Dhabi operates from three sites: (1) Mussafah 21K warehouse (21,000 SQM, 15m high, with selective, VNA, and drive-in racks), (2) KIZAD (KHIA6‑3_4), and (3) Abu Dhabi Airport Freezone. Services include storage, 3PL/4PL, marine logistics, EV transport, drone inspection, and customs clearance."})
    # --- Rack Types in 21K Warehouse ---
    if match([r"rack type|types of rack|racks in warehouse|vna rack|selective rack|drive in rack|aisle width|racking layout|rack system|warehouse racks|rack tyoes|rak types"]):
        return jsonify({"reply": "DSV’s 21K warehouse in Mussafah includes multiple rack systems: Selective racks with 2.95–3.3m aisle width, VNA (Very Narrow Aisle) racks with 1.95m width, and Drive-in racks with 2.0m width. These systems support high-density and selective storage operations."})
    # --- PSN Identification ---
    if match([r"\bpsn\b|who is psn|what is psn|psn client|psn authority|psn abu dhabi"]):
        return jsonify({"reply": "PSN refers to the Federal Authority of Protocol and Strategic Narrative — a VVIP client served by DSV Abu Dhabi through dedicated warehouse chambers, secure handling, and confidentiality-aligned logistics protocols."})
    # --- DSV Completed Projects ---
    if match([r"dsv projects|completed work|client case study|project reference|what projects have you done|logistics projects|recent work|handled jobs"]):
        return jsonify({"reply": "DSV has completed a wide range of projects including Formula 1 logistics, heavy lift deliveries for ADNOC, relocation of full factories, and asset-based 3PL/4PL implementations across the UAE. We specialize in high-complexity logistics, EPC support, and critical timed deliveries."})
    # --- DSV Al Markaz Facility ---
    if match([r"almarkaz|al markaz|markaz warehouse|almarkaz warehouse|sub warehouse.*markaz"]):
        return jsonify({"reply": "DSV operates a sub-warehouse in Al Markaz, Abu Dhabi, with a total covered area of 12,000 sqm. It supports general storage, 3PL activities, and overflow for large-scale industrial clients. Al Markaz complements our main 21K and M44/M45 sites."})
    # --- Single-word and broad DSV Mussafah match ---
    if match([r"\bmussafah\b"]):
        return jsonify({"reply": "DSV's main operations in Mussafah include the 21K warehouse (21,000 SQM, 15m high), sub-warehouses M44 and M45, and our open yard of 360,000 SQM. Services provided include 3PL, 4PL, chemical storage, RMS documentation handling, and project cargo logistics."})
    # --- General Transportation Distance Inquiry ---
    if match([r"destination distance|destinations distances|how far|distance between emirates|transport distances|travel km|uae road distance"]):
        return jsonify({"reply": "Here are some sample transportation distances: Abu Dhabi → Dubai: 140 km, Abu Dhabi → RAK: 240 km, Dubai → Fujairah: 130 km, Sharjah → Ajman: 15 km. Let me know which route you're interested in and I can provide the approximate distance."})
    # --- General Temperature Inquiry ---
    if match([r"\btemperature\b|storage temperature|temp range|how cold|how hot|temperature zones"]):
        return jsonify({"reply": "DSV offers three types of temperature-controlled storage: (1) Ambient zones maintained at +18°C to +25°C, (2) Cold rooms at +2°C to +8°C, and (3) Freezer zones set at –22°C. These options support food, pharmaceuticals, and sensitive cargo."})
    # --- General Truck Types Inquiry ---
    if match([r"truck types|types of trucks|transport fleet|available trucks|transport vehicles|vehicle types"]):
        return jsonify({"reply": "DSV operates a wide range of truck types including flatbeds, double trailers, box trucks, reefers, city trucks, lowbeds, and tippers — each designed to handle different cargo types, delivery zones, and operational needs."})
    # --- General Storage Inquiry ---
    if match([r"\bstorage\b|storage options|warehouse storage|what storage do you offer|types of storage|available storage"]):
        return jsonify({"reply": "DSV offers multiple storage types across Abu Dhabi including AC storage (2.5 AED/CBM/day), Non-AC (2.0), Open Shed (1.8), Chemical AC and Non-AC, and Open Yard (125–160 AED/SQM/year). We also provide temperature-controlled zones, cold rooms, freezers, and full VAS support."})
    # --- VNA Racking System ---
    if match([r"\bvna\b|very narrow aisle|vna rack|narrow aisle rack|vna trucks|vna system|vna setup"]):
        return jsonify({"reply": "VNA stands for Very Narrow Aisle. At DSV’s 21K warehouse in Mussafah, VNA racking offers 1.95m aisle widths for high-density storage and is serviced by specialized VNA forklifts. It's ideal for maximizing pallet positions in limited space."})

    if match([r"\b4pl\b|fourth party logistics|control tower|orchestration|logistics strategy"]):
        return jsonify({"reply": "4PL (Fourth-Party Logistics) means DSV acts as a strategic control tower — managing your full supply chain, including multiple vendors, IT integration, and transport optimization. In the UAE, DSV serves oil & gas clients under 4PL to manage marine charters, warehousing, and compliance across multiple regions."})

    # --- Warehouse Occupancy Inquiries ---
    if match([
    r"(do you have )?space( in)? (the )?(warehouse|facility|storage)",
    r"(warehouse|storage|facility).*(availability|space|capacity|vacancy)",
    r"(available space|free space|can i store|is there room)",
    r"(storage full|warehouse full|occupied|rented out|storage status)"]):
        return jsonify({"reply": "For warehouse occupancy inquiries, please contact Biju Krishnan at biju.krishnan@dsv.com."})

    # --- Transport Rates & Availability ---
    if match([r"(transport|delivery|trucking|fleet|trailer|truck|flatbed|refrigerated|reefer|lowbed|availability|booking).*rate"]):
        return jsonify({"reply": "For transport rates and availability, please contact the OCC team: Ronnell Toring at ronnell.toring@dsv.com."})

    if match([r"(transport availability|truck availability|trailer availability|flatbed available|can you deliver|book a truck|need a truck|truck timing)"]):
        return jsonify({"reply": "For any transportation needs or vehicle availability, kindly reach out to Ronnell Toring at ronnell.toring@dsv.com (DSV OCC team)."})

    # --- Mussafah 21K Warehouse Info ---
    if match([r"21k|main warehouse|mussafah warehouse|dsv warehouse abu dhabi"]):
        return jsonify({"reply": "DSV’s 21K warehouse in Mussafah is 21,000 SQM, 15m clear height. Rack types: Selective (2.95–3.3m aisles), VNA (1.95m), Drive-in (2.0m)."})
    # --- DSV GLOBAL OVERVIEW ---
    if match([r"what is dsv|about dsv|dsv overview|who.*dsv|dsv company|dsv info|dsv profile|dsv background|dsv global"]):
        return jsonify({"reply": "DSV is a global logistics company founded in 1976 in Denmark. It operates in 90+ countries with over 160,000 employees, offering Air & Sea, Road, and Contract Logistics services. DSV is listed on Nasdaq Copenhagen and follows an asset-light model relying on subcontractors."})

    if match([r"dsv.*headquarter|dsv.*location|where is dsv from|dsv based in|dsv hq"]):
        return jsonify({"reply": "DSV's global headquarters is in Hedehusene, Denmark. It started as a Danish haulier group and grew through major acquisitions including UTi, Panalpina, Agility, and DB Schenker."})

    if match([r"dsv.*structure|business model|divisions|organization|dsv.*departments"]):
        return jsonify({"reply": "DSV is structured into three divisions: Air & Sea (freight forwarding), Road (domestic/international trucking), and Solutions (warehousing, 3PL, and 4PL contract logistics)."})

    if match([r"stock|public company|nasdaq|listed|c25 index"]):
        return jsonify({"reply": "Yes, DSV is publicly traded on the Nasdaq Copenhagen exchange, part of the C25 index, with 100% free float and no majority shareholder."})

    if match([r"growth|merger|acquisition|panalpina|agility|uti|schenker"]):
        return jsonify({"reply": "DSV has expanded globally via acquisitions: UTi in 2016, Panalpina in 2019, Agility in 2021, and DB Schenker in 2025 — becoming the world's largest logistics provider."})

    # --- DSV ABU DHABI OVERVIEW ---
    if match([r"abu dhabi|uae.*branch|mussafah.*warehouse|where is 21k|dsv in abu dhabi|dsv mussafah|dsv kizad|dsv airport site"]):
        return jsonify({"reply": "DSV Abu Dhabi operates from three sites: (1) Mussafah 21K warehouse (21,000 SQM, 15m high, with selective, VNA, and drive-in racks), (2) KIZAD (KHIA6‑3_4), and (3) Abu Dhabi Airport Freezone. Services include storage, 3PL/4PL, marine logistics, EV transport, drone inspection, and customs clearance."})

    if match([r"21k|main warehouse|rack type|aisle|clear height"]):
        return jsonify({"reply": "DSV’s main 21K warehouse in Mussafah is 21,000 SQM with 15m clear height. It includes Selective racks (2.95–3.3m aisle), VNA racks (1.95m), and Drive-in racks (2.0m)."})

    if match([r"contact|reach.*dsv|phone number|email.*dsv|support number|how.*call.*dsv"]):
        return jsonify({"reply": "You can reach DSV Abu Dhabi at +971 2 509 9599 or AE.AUHSales@ae.dsv.com. Fax: +971 2 551 4833. Our team can assist with warehousing, transport, and logistics."})

    if match([r"working hours|timing|when open|opening hours|dsv.*open"]):
        return jsonify({"reply": "DSV Abu Dhabi offices operate Monday to Friday from 08:00 AM to 5:00 PM. Saturday operations are limited and subject to request."})
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

    # --- Fallback (never ask to rephrase) ---
    return jsonify({"reply": "I'm trained on everything related to DSV storage, transport, VAS, Mussafah warehouse, and services. Can you try asking again with more detail?"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
