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
    if match([r"\bsme\b", r"sme container", r"what is sme", r"sme size", r"sme container size"]):
        return jsonify({"reply": "In logistics, **SME** usually refers to **Small and Medium-sized Enterprises**, but in some UAE contexts, 'SME container' refers to **customized containers** used by SMEs for small-scale imports or short-term storage.\n\nPlease clarify if you're referring to:\n- SME as a business category\n- Or SME containers used for specialized shipping or modular storage solutions"})

    # --- Pallet Info ---
    if match([r"pallet size|pallet dimension|standard pallet|euro pallet"]):
        return jsonify({"reply": "Standard pallet: 1.2m x 1.0m, Euro pallet: 1.2m x 0.8m. Standard = 14 per bay, Euro = 21 per bay in 21K."})

    # --- VAS Categories ---
    if match([r"standard vas", r"normal vas", r"handling charges", r"pallet charges", r"vas for ac", r"vas for non ac", r"vas for open shed"]):
        return jsonify({"reply": "Standard VAS includes:\n- In/Out Handling: 20 AED/CBM\n- Pallet Loading: 12 AED/pallet\n- Documentation: 125 AED/set\n- Packing with pallet: 85 AED/CBM\n- Inventory Count: 3,000 AED/event\n- Case Picking: 2.5 AED/carton\n- Sticker Labeling: 1.5 AED/label\n- Shrink Wrapping: 6 AED/pallet\n- VNA Usage: 2.5 AED/pallet"})

    if match([r"chemical vas", r"vas for chemical", r"hazmat vas", r"dangerous goods vas"]):
        return jsonify({"reply": "Chemical VAS includes:\n- Handling (Palletized): 20 AED/CBM\n- Handling (Loose): 25 AED/CBM\n- Documentation: 150 AED/set\n- Packing with pallet: 85 AED/CBM\n- Inventory Count: 3,000 AED/event\n- Inner Bag Picking: 3.5 AED/bag\n- Sticker Labeling: 1.5 AED/label\n- Shrink Wrapping: 6 AED/pallet"})

    if match([r"open yard vas", r"yard equipment", r"forklift rate", r"crane rate", r"container lifting", r"yard charges"]):
        return jsonify({"reply": "Open Yard VAS includes:\n- Forklift (3T–7T): 90 AED/hr\n- Forklift (10T): 200 AED/hr\n- Forklift (15T): 320 AED/hr\n- Mobile Crane (50T): 250 AED/hr\n- Mobile Crane (80T): 450 AED/hr\n- Container Lifting: 250 AED/lift\n- Container Stripping (20ft): 1,200 AED/hr"})

    if match([r"\bvas\b", r"\ball vas\b", r"list.*vas", r"show.*vas", r"everything included in vas", r"vas details", r"what.*vas"]):
        return jsonify({"reply": "Which VAS category are you looking for? Please specify:\n- Standard VAS (AC / Non-AC / Open Shed)\n- Chemical VAS\n- Open Yard VAS"})

    # --- Chemical Quotation Required Docs ---
    if match([r"store.*chemical|quotation.*chemical|data.*chemical|requirement.*chemical"]):
        return jsonify({"reply": "To quote for chemical storage, we need:\n- Material name\n- Hazard class\n- CBM\n- Period\n- MSDS (Material Safety Data Sheet)."})
    if match([r"proposal|quotation|quote.*open yard|send me.*quote|how to get quote|need.*quotation"]):
        return jsonify({"reply": "To get a full quotation, please close this chat and fill the details in the main form on the left. The system will generate a downloadable document for you."})

    # --- Standard VAS Calculation  ---
    if match([r"calculate.*pallet loading", r"pallet loading.*\d+", r"loading.*\d+ pallet"]):
    qty = re.search(r"(\d+)", message)
        if qty:
        total = int(qty.group(1)) * 12
            return jsonify({"reply": f"Pallet Loading for {qty.group(1)} pallets at 12 AED/pallet = {total:,.2f} AED."})

    if match([r"calculate.*packing with pallet", r"packing.*\d+ pallet"]):
    qty = re.search(r"(\d+)", message)
        if qty:
        total = int(qty.group(1)) * 85
            return jsonify({"reply": f"Packing with pallet for {qty.group(1)} pallets at 85 AED/CBM = {total:,.2f} AED."})

    if match([r"calculate.*documentation", r"docs.*\d+", r"documentation.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 125
        return jsonify({"reply": f"Documentation for {qty.group(1)} sets at 125 AED/set = {total:,.2f} AED."})

    if match([r"calculate.*case picking", r"case picking.*\d+", r"carton picking.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 2.5
        return jsonify({"reply": f"Case Picking for {qty.group(1)} cartons at 2.5 AED/carton = {total:,.2f} AED."})

    if match([r"calculate.*inventory count", r"inventory count.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 3000
        return jsonify({"reply": f"Inventory Count for {qty.group(1)} events at 3,000 AED/event = {total:,.2f} AED."})

    if match([r"calculate.*sticker", r"labeling.*\d+", r"stickers.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 1.5
        return jsonify({"reply": f"Sticker Labeling for {qty.group(1)} labels at 1.5 AED/label = {total:,.2f} AED."})

    if match([r"calculate.*shrink", r"shrink wrapping.*\d+", r"shrink.*\d+ pallet"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 6
        return jsonify({"reply": f"Shrink Wrapping for {qty.group(1)} pallets at 6 AED/pallet = {total:,.2f} AED."})

    if match([r"calculate.*vna", r"vna.*\d+", r"vna usage.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 2.5
        return jsonify({"reply": f"VNA Usage for {qty.group(1)} pallets at 2.5 AED/pallet = {total:,.2f} AED."})

# --- Chemical VAS Calculations ---

    if match([r"calculate.*chemical.*handling.*pallet", r"chemical.*pallet.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 20
        return jsonify({"reply": f"Chemical Handling (Palletized) for {qty.group(1)} pallets at 20 AED/CBM = {total:,.2f} AED."})

    if match([r"calculate.*chemical.*handling.*loose", r"chemical.*loose.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 25
        return jsonify({"reply": f"Chemical Handling (Loose) for {qty.group(1)} CBM at 25 AED/CBM = {total:,.2f} AED."})

    if match([r"calculate.*inner bag picking", r"bag picking.*\d+", r"inner bags.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 3.5
        return jsonify({"reply": f"Inner Bag Picking for {qty.group(1)} bags at 3.5 AED/bag = {total:,.2f} AED."})

    if match([r"calculate.*chemical.*documentation", r"chemical.*docs.*\d+", r"chemical.*documentation.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 150
        return jsonify({"reply": f"Chemical Documentation for {qty.group(1)} sets at 150 AED/set = {total:,.2f} AED."})

    if match([r"calculate.*chemical.*packing", r"chemical.*packing.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 85
        return jsonify({"reply": f"Packing with pallet for {qty.group(1)} CBM at 85 AED/CBM = {total:,.2f} AED."})

    if match([r"calculate.*chemical.*inventory count", r"chemical.*inventory.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 3000
        return jsonify({"reply": f"Inventory Count for {qty.group(1)} events at 3,000 AED/event = {total:,.2f} AED."})

    if match([r"calculate.*chemical.*label", r"chemical.*sticker.*\d+", r"chemical.*labeling.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 1.5
        return jsonify({"reply": f"Sticker Labeling for {qty.group(1)} labels at 1.5 AED/label = {total:,.2f} AED."})

    if match([r"calculate.*chemical.*shrink", r"chemical.*shrink wrap.*\d+", r"chemical.*shrink.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 6
        return jsonify({"reply": f"Shrink Wrapping for {qty.group(1)} pallets at 6 AED/pallet = {total:,.2f} AED."})


    # --- Open Yard VAS Calculations ---
    if match([r"calculate.*forklift.*3", r"forklift 3t.*\d+", r"3 ton forklift.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 90
        return jsonify({"reply": f"Forklift (3T–7T) usage for {qty.group(1)} hours at 90 AED/hr = {total:,.2f} AED."})

    if match([r"calculate.*forklift.*10", r"forklift 10t.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 200
        return jsonify({"reply": f"Forklift (10T) usage for {qty.group(1)} hours at 200 AED/hr = {total:,.2f} AED."})

    if match([r"calculate.*forklift.*15", r"forklift 15t.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 320
        return jsonify({"reply": f"Forklift (15T) usage for {qty.group(1)} hours at 320 AED/hr = {total:,.2f} AED."})

    if match([r"calculate.*crane.*50", r"crane 50t.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 250
        return jsonify({"reply": f"Mobile Crane (50T) usage for {qty.group(1)} hours at 250 AED/hr = {total:,.2f} AED."})

    if match([r"calculate.*crane.*80", r"crane 80t.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 450
        return jsonify({"reply": f"Mobile Crane (80T) usage for {qty.group(1)} hours at 450 AED/hr = {total:,.2f} AED."})

    if match([r"calculate.*container lifting", r"container.*lift.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 250
        return jsonify({"reply": f"Container Lifting for {qty.group(1)} lifts at 250 AED/lift = {total:,.2f} AED."})

    if match([r"calculate.*container stripping", r"stripping.*20ft.*\d+"]):
    qty = re.search(r"(\d+)", message)
    if qty:
        total = int(qty.group(1)) * 1200
        return jsonify({"reply": f"Container Stripping (20ft) for {qty.group(1)} hours at 1,200 AED/hr = {total:,.2f} AED."})
    # --- 21K Warehouse  ---
    if match([r"rack height|rack levels|pallets per bay|rack system"]):
        return jsonify({"reply": "21K warehouse racks are 12m tall with 6 pallet levels. Each bay holds 14 Standard pallets or 21 Euro pallets."})
    if match([r"\b21k\b", r"tell me about 21k", r"what is 21k", r"21k warehouse", r"21k dsv", r"main warehouse", r"mussafah.*21k"]):
        return jsonify({"reply": "21K is DSV’s main warehouse in Mussafah, Abu Dhabi. It is 21,000 sqm with a clear height of 15 meters. The facility features:\n- 3 rack types: Selective, VNA, and Drive-in\n- Rack height: 12m with 6 pallet levels\n- Aisle widths: Selective (2.95–3.3m), VNA (1.95m), Drive-in (2.0m)\n- 7 chambers used by clients like ADNOC, ZARA, PSN, and Civil Defense\n- Fully equipped with fire systems, access control, and RMS for document storage."})
    if match([r"\bgdsp\b", r"what is gdsp", r"gdsp certified", r"gdsp warehouse", r"gdsp compliance"]):
        return jsonify({"reply": "GDSP stands for Good Distribution and Storage Practices. It ensures that warehouse operations comply with global standards for the safe handling, storage, and distribution of goods, especially pharmaceuticals and sensitive materials. DSV’s warehouses in Abu Dhabi are GDSP certified."})
    if match([r"\biso\b", r"what iso", r"iso certified", r"tell me about iso", r"dsv iso", r"which iso standards"]):
        return jsonify({"reply": "DSV facilities in Abu Dhabi are certified with multiple ISO standards:\n- **ISO 9001**: Quality Management\n- **ISO 14001**: Environmental Management\n- **ISO 45001**: Occupational Health & Safety\nThese certifications ensure that DSV operates to the highest international standards in safety, service quality, and environmental responsibility."})
    if match([r"\bgdp\b", r"what is gdp", r"gdp warehouse", r"gdp compliant", r"gdp certified"]):
        return jsonify({"reply": "GDP stands for **Good Distribution Practice**, a quality standard for warehouse and transport operations of pharmaceutical products. DSV’s healthcare storage facilities in Abu Dhabi, including the Airport Freezone warehouse, are GDP-compliant, ensuring cold chain integrity, traceability, and regulatory compliance."})
    if match([r"cold chain", r"what.*cold chain", r"cold storage", r"temperature zones", r"what.*chains.*temperature", r"freezer room", r"cold room", r"ambient storage"]):
        return jsonify({"reply": "DSV offers full temperature-controlled logistics including:\n\n🟢 **Ambient Storage**: +18°C to +25°C (for general FMCG, electronics, and dry goods)\n🔵 **Cold Room**: +2°C to +8°C (for pharmaceuticals, healthcare, and food products)\n🔴 **Freezer Room**: –22°C (for frozen goods and sensitive biological materials)\n\nOur warehouses in Abu Dhabi are equipped with temperature monitoring, backup power, and GDP-compliant systems to maintain cold chain integrity."})

    # --- 21K HSE  ---
    if match([r"\bqhse\b", r"quality health safety environment", r"qhse policy", r"qhse standards", r"dsv qhse"]):
        return jsonify({"reply": "DSV follows strict QHSE standards across all operations. This includes:\n- Quality checks (ISO 9001)\n- Health & safety compliance (ISO 45001)\n- Environmental management (ISO 14001)\nAll staff undergo QHSE training, and warehouses are equipped with emergency protocols, access control, firefighting systems, and first-aid kits."})
    if match([r"\bhse\b", r"health safety environment", r"dsv hse", r"hse policy", r"hse training"]):
        return jsonify({"reply": "DSV places strong emphasis on HSE compliance. We implement:\n- Safety inductions and daily toolbox talks\n- Fire drills and emergency response training\n- PPE usage and incident reporting procedures\n- Certified HSE officers across sites\nWe’re committed to zero harm in the workplace."})
    if match([r"training", r"staff training", r"employee training", r"warehouse training", r"qhse training"]):
        return jsonify({"reply": "All DSV warehouse and transport staff undergo structured training programs, including:\n- QHSE training (Safety, Fire, First Aid)\n- Equipment handling (Forklifts, Cranes, VNA)\n- WMS and inventory systems\n- Customer service and operational SOPs\nRegular refresher courses are also conducted."})
    if match([r"\bdg\b", r"dangerous goods", r"hazardous material", r"hazmat", r"hazard class", r"dg storage"]):
        return jsonify({"reply": "Yes, DSV handles **DG (Dangerous Goods)** and hazardous materials in specialized chemical storage areas. We comply with all safety and documentation requirements including:\n- Hazard classification and labeling\n- MSDS (Material Safety Data Sheet) submission\n- Trained staff for chemical handling\n- Temperature-controlled and fire-protected zones\n- Secure access and emergency systems\n\nPlease note: For a DG quotation, we require the **material name, hazard class, CBM, period, and MSDS**."})

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
    if match([r"storage rate[s]?$", r"\brates\b", r"storage cost", r"how much.*storage", r"quotation.*storage only"]):
        return jsonify({"reply": "Which type of storage are you asking about? AC, Non-AC, Open Shed, Chemicals, or Open Yard?"})
    if match([r"standard ac", r"ac standard"]):
        return jsonify({"reply": "Standard AC storage is 2.5 AED/CBM/day. Standard VAS applies."})
    if match([r"\bstandard\b$", r"\bstandard storage\b$", r"only standard"]):
        return jsonify({"reply": "Do you mean *Standard AC*, *Standard Non-AC*, or *Open Shed* storage? Please specify."})
    if match([r"\bchemical\b$", r"\bchemical storage\b$", r"only chemical"]):
        return jsonify({"reply": "Do you mean *Chemical AC* or *Chemical Non-AC*? Let me know which one you need the rate for."})
    if match([r"\bac\b$", r"\bac storage\b$", r"only ac"]):
        return jsonify({"reply": "Do you mean *Standard AC* storage or *Chemical AC* storage?"})

    if match([r"chemical ac", r"ac chemical"]):
        return jsonify({"reply": "Chemical AC storage is 3.5 AED/CBM/day. Chemical VAS applies."})

    if match([r"standard non ac", r"non ac standard"]):
        return jsonify({"reply": "Standard Non-AC storage is 2.0 AED/CBM/day. Standard VAS applies."})

    if match([r"chemical non ac", r"non ac chemical"]):
        return jsonify({"reply": "Chemical Non-AC storage is 2.7 AED/CBM/day. Chemical VAS applies."})

    if match([r"open shed", r"standard open shed"]):
        return jsonify({"reply": "Open Shed storage is 1.8 AED/CBM/day. Standard VAS applies."})
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
    if match([r"what is dsv", r"who is dsv", r"tell me about dsv", r"dsv overview", r"\bdsv\b only"]):
        return jsonify({"reply": "DSV stands for 'De Sammensluttede Vognmænd', meaning 'The Consolidated Hauliers' in Danish. Founded in 1976, DSV is a global logistics leader offering transport, warehousing, and supply chain solutions in over 80 countries. It's publicly listed on Nasdaq Copenhagen and serves industries like FMCG, oil & gas, pharma, retail, and more."})
    if match([r"what (do|does) (they|dsv) do", r"what (they|dsv) offer", r"dsv.*services", r"dsv.*specialize", r"who.*dsv.*and.*do", r"dsv operations", r"dsv.*work in", r"services.*dsv"]):
        return jsonify({"reply": "DSV provides end-to-end logistics solutions including:\n- Freight forwarding (air, sea, road)\n- Warehousing (ambient, cold chain, chemical)\n- Transportation & distribution across the UAE and GCC\n- 3PL & 4PL supply chain management\n- Customs clearance and documentation\n- Specialized services for healthcare, FMCG, oil & gas, retail, and e-commerce."})
    if match([r"what is dsv", r"who is dsv", r"tell me about dsv", r"dsv overview", r"\bdsv\b only"]):
        return jsonify({"reply": "DSV stands for 'De Sammensluttede Vognmænd', meaning 'The Consolidated Hauliers' in Danish. Founded in 1976, DSV is a global logistics leader offering transport, warehousing, and supply chain solutions in over 80 countries. It’s listed on Nasdaq Copenhagen and serves diverse industries like FMCG, oil & gas, pharma, and retail."})

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
    if match([r"warehouse temp|temperature.*zone|storage temperature|cold room|freezer|ambient temp|warehouse temperature"]):
        return jsonify({"reply": "DSV provides 3 temperature zones:\n- **Ambient**: +18°C to +25°C\n- **Cold Room**: +2°C to +8°C\n- **Freezer**: –22°C\nThese zones are used for FMCG, pharmaceuticals, and temperature-sensitive products."})
    if match([r"size of our warehouse|total warehouse area|total sqm|warehouse size|how big.*warehouse"]):
        return jsonify({"reply": "DSV Abu Dhabi has approx. **44,000 sqm** of warehouse space:\n- 21K in Mussafah (21,000 sqm)\n- M44 (5,760 sqm)\n- M45 (5,000 sqm)\n- Al Markaz in Hameem (12,000 sqm)\nPlus 360,000 sqm of open yard."})

    # --- Machinery / Machineries ---
    if match([r"machinery|machineries|machines used|equipment used"]):
        return jsonify({"reply": "DSV uses forklifts (3–15T), VNA, reach trucks, pallet jacks, cranes, and container lifters in warehouse and yard operations."})
# --- Mussafah 21K Warehouse Info ---
    if match([r"21k.*rack height|rack height.*21k"]):
        return jsonify({"reply": "The racks in the 21K warehouse in Mussafah are 12 meters high, with 6 pallet levels plus ground. DSV uses both Euro and Standard pallets. Each bay holds up to 14 Standard pallets or 21 Euro pallets."})
    if match([r"rack height|rack types|type of racks|tell me.*racks|rack info"]):
        return jsonify({"reply": "The 21K warehouse has 3 types of racking systems:\n- **Selective racks**: Aisle width 2.95m–3.3m\n- **VNA (Very Narrow Aisle)**: Aisle width 1.95m\n- **Drive-in racks**: Aisle width 2.0m\nAll racks are 12 meters tall with 6 pallet levels."})
    if match([r"\bmhe\b", r"equipment used", r"machineries", r"machines", r"warehouse tools"]):
        return jsonify({"reply": "MHE (Material Handling Equipment) used at DSV includes forklifts (3–15T), VNA trucks, reach trucks, pallet jacks, mobile cranes, and container lifters."})

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
    # --- Transportation---
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
    if match([r"\bmsds\b|material safety data sheet|chemical data"]):
        return jsonify({"reply": "Yes, MSDS (Material Safety Data Sheet) is mandatory for any chemical storage inquiry. It ensures safe handling and classification of the materials stored in DSV’s facilities."})
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
        # --- DSV Abu Dhabi Facility Sizes ---
    if match([
        r"plot size", r"abu dhabi total area", r"site size", r"facility size", r"total sqm", r"how big",
        r"yard size", r"open yard area", r"size of open yard", r"open yard.*size", r"area of open yard"]):
        return jsonify({"reply": "DSV Abu Dhabi's open yard spans 360,000 SQM across Mussafah and KIZAD. The total logistics plot is 481,000 SQM, including 100,000 SQM of service roads and utilities, and a 21,000 SQM warehouse (21K)."})

    if match([r"sub warehouse|m44|m45|al markaz|abu dhabi warehouse total|all warehouses"]):
        return jsonify({"reply": "In addition to the main 21K warehouse, DSV operates sub-warehouses in Abu Dhabi: M44 (5,760 sqm), M45 (5,000 sqm), and Al Markaz (12,000 sqm). Combined with 21K, the total covered warehouse area in Abu Dhabi is approximately 44,000 sqm."})

    if match([r"terms and conditions|quotation policy|billing cycle|operation timing|payment terms|quotation validity"]):
        return jsonify({"reply": "DSV quotations include the following terms: Monthly billing, final settlement before vacating, 15-day quotation validity, subject to space availability. The depot operates Monday–Friday 8:30 AM to 5:30 PM. Insurance is not included by default. An environmental fee of 0.15% is added to all invoices. Non-moving cargo over 3 months may incur extra storage tariff."})
    # --- QHSE ---   
    if match([r"safety training|warehouse training|fire drill|manual handling|staff safety|employee training|toolbox talk"]):
        return jsonify({"reply": "DSV staff undergo regular training in fire safety, first aid, manual handling, emergency response, and site induction. We also conduct toolbox talks and refresher sessions to maintain safety awareness and operational excellence."})
    # --- DSV & ADNOC Relationship ---
    if match([r"adnoc|adnoc project|dsv.*adnoc|oil and gas project|dsv support.*adnoc|logistics for adnoc"]):
        return jsonify({"reply": "DSV has an active relationship with ADNOC and its group companies, supporting logistics for Oil & Gas projects across Abu Dhabi. This includes warehousing of chemicals, fleet transport to remote sites, 3PL for EPC contractors, and marine logistics for ADNOC ISLP and offshore projects. All operations are QHSE compliant and meet ADNOC’s safety and performance standards."})
    # --- UAE Summer Midday Break ---
    if match([r"summer break|midday break|working hours summer|12.*3.*break|uae heat ban|no work afternoon|hot season schedule"]):
        return jsonify({"reply": "DSV complies with UAE summer working hour restrictions. From June 15 to September 15, all outdoor work (including open yard and transport loading) is paused daily between 12:30 PM and 3:30 PM. This ensures staff safety and follows MOHRE guidelines."})
    # --- Client Name Queries ---
    if match([r"chambers.*21k", r"how many.*chambers", r"clients.*warehouse", r"who.*in.*warehouse", r"21k.*clients", r"tell me.*chambers", r"\bchambers\b"]):
        return jsonify({"reply": "There are 7 chambers in the 21K warehouse:\n- **Chamber 1**: Khalifa University\n- **Chamber 2**: PSN\n- **Chamber 3**: Food clients & fast-moving items\n- **Chamber 4**: MCC, TR, and ADNOC\n- **Chamber 5**: PSN\n- **Chamber 6**: ZARA & TR\n- **Chamber 7**: Civil Defense and RMS"})

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
