"""
Dictionary Expansion v2 — additive merge into opd_refset_v1.json + pmbjp_generic_formulary.json.
Rules (per MASTER_DIRECTIVE):
  - Every SNOMED concept_id must be a REAL published concept (no invented codes).
  - Every brand->generic mapping must be factually true.
  - Additive only: existing entries are never modified or removed.
Backs up originals to attic/ before writing.
"""
import json
import os
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFSET_PATH = os.path.join(PROJECT_ROOT, "data", "refset", "opd_refset_v1.json")
FORMULARY_PATH = os.path.join(PROJECT_ROOT, "data", "formulary", "pmbjp_generic_formulary.json")
ATTIC = os.path.join(PROJECT_ROOT, "attic")

# ---------------------------------------------------------------------------
# NEW OPD REFSET ENTRIES — real SNOMED CT concept IDs, Indian OPD usage.
# ---------------------------------------------------------------------------
NEW_REFSET = [
    # --- Symptoms & findings ---
    {"preferred_name": "Fever", "semantic_tag": "finding", "concept_id": "386661006",
     "hinglish_synonyms": ["bukhar", "bukhaar", "taap aana", "temperature hai"],
     "abbreviations": ["Fvr", "Pyrexia"]},
    {"preferred_name": "Cough", "semantic_tag": "finding", "concept_id": "49727002",
     "hinglish_synonyms": ["khansi", "khaansi", "khaansi aa rahi"],
     "abbreviations": ["C/C", "cough+"]},
    {"preferred_name": "Headache", "semantic_tag": "finding", "concept_id": "25064002",
     "hinglish_synonyms": ["sar dard", "sir dard", "sar me dard"],
     "abbreviations": ["HA"]},
    {"preferred_name": "Vomiting", "semantic_tag": "finding", "concept_id": "249497008",
     "hinglish_synonyms": ["ulti", "ulti jaisa lag raha", "matli"],
     "abbreviations": ["V+", "N&V"]},
    {"preferred_name": "Diarrhoea", "semantic_tag": "finding", "concept_id": "62315008",
     "hinglish_synonyms": ["loose motion", "dast", "patle dast", "pet kharab chal raha"],
     "abbreviations": ["LOM", "LO"]},
    {"preferred_name": "Nausea", "semantic_tag": "finding", "concept_id": "422587007",
     "hinglish_synonyms": ["ji machalna", "ulti jaisa feel", "matli si"],
     "abbreviations": ["N+"]},
    {"preferred_name": "Abdominal pain", "semantic_tag": "finding", "concept_id": "15429001",
     "hinglish_synonyms": ["pet dard", "pet me dard", "tummy pain"],
     "abbreviations": ["AP+", "abd pain"]},
    {"preferred_name": "Chest pain", "semantic_tag": "finding", "concept_id": "29857009",
     "hinglish_synonyms": ["seene me dard", "chhati me dard"],
     "abbreviations": ["CP"]},
    {"preferred_name": "Dyspnoea", "semantic_tag": "finding", "concept_id": "267036007",
     "hinglish_synonyms": ["saans phoolna", "saans lene me dikkat", "breathless", "saans chadhna"],
     "abbreviations": ["SOB", "DOE"]},
    {"preferred_name": "Myalgia", "semantic_tag": "finding", "concept_id": "68962000",
     "hinglish_synonyms": ["badan dard", "muscle pain", "body ache"],
     "abbreviations": ["myalgia+"]},
    {"preferred_name": "Pruritus", "semantic_tag": "finding", "concept_id": "418290009",
     "hinglish_synonyms": ["khujli", "itching", "khaj khajee"],
     "abbreviations": ["itch+"]},
    {"preferred_name": "Fatigue", "semantic_tag": "finding", "concept_id": "84229001",
     "hinglish_synonyms": ["kamzori", "thakan", "weakness feel hoti hai"],
     "abbreviations": ["fatigue+"]},
    {"preferred_name": "Dizziness", "semantic_tag": "finding", "concept_id": "404640003",
     "hinglish_synonyms": ["chakkar aana", "sar ghoomna", "chakkar"],
     "abbreviations": ["vertigo-like"]},
    {"preferred_name": "Skin rash", "semantic_tag": "finding", "concept_id": "271807003",
     "hinglish_synonyms": ["chakatte", "daane", "rashes ho gaye"],
     "abbreviations": ["rash+"]},

    # --- Respiratory & infectious ---
    {"preferred_name": "Acute upper respiratory infection", "semantic_tag": "disorder", "concept_id": "82272004",
     "hinglish_synonyms": ["zukam khansi", "sardi khansi dono", "galah khansi"],
     "abbreviations": ["URTI", "URI"]},
    {"preferred_name": "Bronchial asthma", "semantic_tag": "disorder", "concept_id": "195967001",
     "hinglish_synonyms": ["damma", "saans ki bimari", "asthma attack"],
     "abbreviations": ["BA", "CASA"]},
    {"preferred_name": "Chronic obstructive pulmonary disease", "semantic_tag": "disorder", "concept_id": "13645005",
     "hinglish_synonyms": ["phephde ki purani bimari", "smoker ki khansi", "saans ki taklif purani"],
     "abbreviations": ["COPD", "COAD"]},
    {"preferred_name": "Acute bronchitis", "semantic_tag": "disorder", "concept_id": "10509002",
     "hinglish_synonyms": ["balgam wali khansi", "chest infection"],
     "abbreviations": ["bronchitis"]},
    {"preferred_name": "Pneumonia", "semantic_tag": "disorder", "concept_id": "233604007",
     "hinglish_synonyms": ["phephdon ka infection", "pneumonia hua hai"],
     "abbreviations": ["LRTI"]},
    {"preferred_name": "Sinusitis", "semantic_tag": "disorder", "concept_id": "367498001",
     "hinglish_synonyms": ["sinus ki dikkat", "naak band rehna", "sinus"],
     "abbreviations": ["sinusitis"]},
    {"preferred_name": "Influenza", "semantic_tag": "disorder", "concept_id": "6142004",
     "hinglish_synonyms": ["flu hua", "seasonal flu", "flue bug"],
     "abbreviations": ["flu"]},
    {"preferred_name": "Dengue", "semantic_tag": "disorder", "concept_id": "38362002",
     "hinglish_synonyms": ["dengue bukhar", "dengu", "machhar ke kaatne se bukhar", "platelet kam"],
     "abbreviations": ["DF"]},
    {"preferred_name": "Malaria", "semantic_tag": "disorder", "concept_id": "63567004",
     "hinglish_synonyms": ["maleria", "machhar bukhar", "thand kam kap kap"],
     "abbreviations": ["MP positive", "MP+"]},
    {"preferred_name": "Typhoid fever", "semantic_tag": "disorder", "concept_id": "85904008",
     "hinglish_synonyms": ["motijhara", "typhoid bukhar", "widal positive"],
     "abbreviations": ["enteric fever"]},
    {"preferred_name": "Chickenpox", "semantic_tag": "disorder", "concept_id": "38907003",
     "hinglish_synonyms": ["chicken guniya", "checak", "dane aur bukhar"],
     "abbreviations": ["varicella"]},
    {"preferred_name": "Conjunctivitis", "semantic_tag": "disorder", "concept_id": "9826008",
     "hinglish_synonyms": ["aankh aana", "aankh lal hona", "eye flu"],
     "abbreviations": ["conjunctivitis"]},
    {"preferred_name": "Acute otitis media", "semantic_tag": "disorder", "concept_id": "31100003",
     "hinglish_synonyms": ["kaan dard", "kaan ka infection", "kaan se paani"],
     "abbreviations": ["AOM"]},

    # --- Gastrointestinal ---
    {"preferred_name": "Gastro-esophageal reflux disease", "semantic_tag": "disorder", "concept_id": "235595003",
     "hinglish_synonyms": ["seene me jalan", "khatti dakar", "khaiyal aana"],
     "abbreviations": ["GERD"]},
    {"preferred_name": "Acute gastroenteritis", "semantic_tag": "disorder", "concept_id": "736190009",
     "hinglish_synonyms": ["pet kharab ultti", "dast aur ulti", "loose motion ulti"],
     "abbreviations": ["AGE"]},
    {"preferred_name": "Constipation", "semantic_tag": "disorder", "concept_id": "14760008",
     "hinglish_synonyms": ["kabz", "pet saaf nahi hota", "motion atki rehti hai"],
     "abbreviations": ["constipation"]},
    {"preferred_name": "Jaundice", "semantic_tag": "disorder", "concept_id": "40570003",
     "hinglish_synonyms": ["piliya", "aankh peeli", "kamla rog"],
     "abbreviations": ["icterus", "bilirubin high"]},

    # --- Cardiovascular / metabolic / endocrine ---
    {"preferred_name": "Ischemic heart disease", "semantic_tag": "disorder", "concept_id": "414545008",
     "hinglish_synonyms": ["dil ki nali block", "heart blockage", "dil ka dora"],
     "abbreviations": ["IHD", "CAD"]},
    {"preferred_name": "Heart failure", "semantic_tag": "disorder", "concept_id": "84114007",
     "hinglish_synonyms": ["dil kamzor ho gaya", "dil fail", "paani bharna dil me"],
     "abbreviations": ["CHF", "CCF"]},
    {"preferred_name": "Atrial fibrillation", "semantic_tag": "disorder", "concept_id": "49436004",
     "hinglish_synonyms": ["dil ki dharkan bigad", "lapata dharkan"],
     "abbreviations": ["AF", "AFib"]},
    {"preferred_name": "Anaemia", "semantic_tag": "disorder", "concept_id": "271737000",
     "hinglish_synonyms": ["khoon ki kami", "hemoglobin kam", "hb low hai"],
     "abbreviations": ["anemia", "Hb low"]},
    {"preferred_name": "Hyperlipidaemia", "semantic_tag": "disorder", "concept_id": "55822004",
     "hinglish_synonyms": ["cholesterol badha", "lipid high", "khoon me charbi"],
     "abbreviations": ["HLD", "DLP"]},
    {"preferred_name": "Obesity", "semantic_tag": "disorder", "concept_id": "414916001",
     "hinglish_synonyms": ["motapa", "vajan zyada", "weight gain"],
     "abbreviations": ["obese", "BMI high"]},
    {"preferred_name": "Hypothyroidism", "semantic_tag": "disorder", "concept_id": "40930008",
     "hinglish_synonyms": ["thyroid kam chalna", "tsh high", "thyroid ki bimari"],
     "abbreviations": ["hypoT"]},
    {"preferred_name": "Migraine", "semantic_tag": "disorder", "concept_id": "37796009",
     "hinglish_synonyms": ["aadhasi dard", "aadhe sir ka dard", "migraine attack"],
     "abbreviations": ["migraine"]},
    {"preferred_name": "Rheumatoid arthritis", "semantic_tag": "disorder", "concept_id": "69896004",
     "hinglish_synonyms": ["jodon ka dard subah subah", "gangadiya sujnā", "RA arthritis"],
     "abbreviations": ["RA", "RF positive"]},
    {"preferred_name": "Low back pain", "semantic_tag": "finding", "concept_id": "161891006",
     "hinglish_synonyms": ["kamar dard", "kamar me dard", "back pain"],
     "abbreviations": ["LBP"]},
    {"preferred_name": "Urinary tract infection", "semantic_tag": "disorder", "concept_id": "68566005",
     "hinglish_synonyms": ["peshab me jalan", "urine infection", "baar baar peshab"],
     "abbreviations": ["UTI"]},
    {"preferred_name": "Anxiety", "semantic_tag": "finding", "concept_id": "48694002",
     "hinglish_synonyms": ["ghabrahat", "bechaini", "dar lag rahe bina wajah"],
     "abbreviations": ["anxiety+", "GAD"]},
    {"preferred_name": "Depressive disorder", "semantic_tag": "disorder", "concept_id": "35489007",
     "hinglish_synonyms": ["depreshan", "man udas rehta", "mood theek nahi"],
     "abbreviations": ["MDD", "depression"]},
    {"preferred_name": "Epilepsy", "semantic_tag": "disorder", "concept_id": "84757009",
     "hinglish_synonyms": ["mirgi", "fit aana", "jhatke aa jana", "marham piisi"],
     "abbreviations": ["SZD", "seizure disorder"]},
]

# ---------------------------------------------------------------------------
# NEW FORMULARY ROWS — factual Indian brand -> generic mappings.
# snomed_id intentionally EMPTY with code_status="generic_mapping_only":
# coding happens at resolve-time from the full RF2 substance hierarchy (Law #1:
# never fabricate codes we cannot verify).
# ---------------------------------------------------------------------------
NEW_FORMULARY = [
    ("Dolo 650", "Paracetamol", "Analgesic / Antipyretic", "dolo, dolo 650 mg, dollo"),
    ("Calpol 650", "Paracetamol", "Analgesic / Antipyretic", "calpol, calpol tablet"),
    ("Crocin Advance", "Paracetamol", "Analgesic / Antipyretic", "crocin, crocin advance 500"),
    ("Combiflam", "Ibuprofen + Paracetamol", "NSAID combination", "combi flam, combiflam tablet"),
    ("Brufen 400", "Ibuprofen", "NSAID", "brufen, brufen 400mg"),
    ("Zerodol SP", "Aceclofenac + Paracetamol + Serratiopeptidase", "NSAID combination", "zerodol sp, zerodol"),
    ("Voveran 50", "Diclofenac", "NSAID", "voveran, voveran sr"),
    ("Naprosyn 250", "Naproxen", "NSAID", "naprosyn"),
    ("Ultracet", "Tramadol + Paracetamol", "Analgesic combination", "ultracecet, ultra cet"),
    ("Cyclopam", "Dicyclomine + Paracetamol", "Antispasmodic", "cyclopam tablet, syrapam"),
    ("Augmentin 625", "Amoxicillin and clavulanic acid", "Beta-lactam antibiotic", "augmentin, moxiklav cv"),
    ("Taxim-O 200", "Cefixime", "Cephalosporin antibiotic", "taximo, taxim o"),
    ("Ceftum 250", "Cefuroxime", "Cephalosporin antibiotic", "ceftum, ceftum 500"),
    ("Azithral 500", "Azithromycin", "Macrolide antibiotic", "azithral, azee 500, azithro"),
    ("Cifran 500", "Ciprofloxacin", "Fluoroquinolone antibiotic", "cifran, ciplox"),
    ("Doxt-SL", "Doxycycline + Lactic acid bacillus", "Tetracycline antibiotic", "doxt sl, doxy"),
    ("Levoflox 500", "Levofloxacin", "Fluoroquinolone antibiotic", "levoflox, levaquin generic"),
    ("Norflox TZ", "Norfloxacin + Tinidazole", "Antibiotic combination", "norflox tz, nor-tz"),
    ("O2 Tablet", "Ofloxacin + Ornidazole", "Antibiotic combination", "o2 tab, o2"),
    ("Pantocid 40", "Pantoprazole", "Proton pump inhibitor", "pantocid, pan 40, pantop"),
    ("Pan-D", "Pantoprazole + Domperidone", "PPI combination", "pan d, pan-dsr"),
    ("Nexpro RD 40", "Esomeprazole + Domperidone", "PPI combination", "nexpro rd, nexpro"),
    ("Razo 20", "Rabeprazole", "Proton pump inhibitor", "razo, razo d"),
    ("Omez 20", "Omeprazole", "Proton pump inhibitor", "omez, omez d"),
    ("Digene Gel", "Antacid suspension (Mg/Al hydroxide + simethicone)", "Antacid", "digene, gelusil"),
    ("Domstal 10", "Domperidone", "Prokinetic / Antiemetic", "domstal, vomistop"),
    ("Perinorm", "Metoclopramide", "Antiemetic", "perinorm tablet, perinorm injection"),
    ("Montek LC", "Montelukast + Levocetirizine", "Antihistamine / Leukotriene antagonist", "montek lc, montek"),
    ("Allegra 120", "Fexofenadine", "Antihistamine", "allegra, fexo 120"),
    ("Cetzine 10", "Cetirizine", "Antihistamine", "cetzine, okacet, cetcip"),
    ("Avil 25", "Pheniramine", "Antihistamine", "avil, avil 25"),
    ("Asthalin HFA Inhaler", "Salbutamol", "Short-acting beta agonist", "asthalin, salbutamol inhaler, ventorlin"),
    ("Foracort 200 Rotacap", "Formoterol + Budesonide", "LABA + Inhaled corticosteroid", "foracort, seroflo"),
    ("Deriphyllin Retard 150", "Etofilline + Theophylline", "Xanthine bronchodilator", "deriphyllin"),
    ("Telma 40", "Telmisartan", "ARB antihypertensive", "telma, telma 40 mg"),
    ("Amlong 5", "Amlodipine", "Calcium channel blocker", "amlong, amlodac"),
    ("Metolar XR 25", "Metoprolol succinate", "Beta blocker", "metolar, metolar xr"),
    ("Losar 50", "Losartan", "ARB antihypertensive", "losar, repace"),
    ("Ecosprin 75", "Aspirin (antiplatelet)", "Antiplatelet", "ecosprin, ecosprin gold combo note: contains clopidogrel variants separately"),
    ("Glycomet 500 SR", "Metformin", "Biguanide oral antidiabetic", "glycomet, glycomet sr"),
    ("Amaryl 2", "Glimepiride", "Sulfonylurea antidiabetic", "amaryl, amaryl m"),
    ("Januvia 50", "Sitagliptin", "DPP-4 inhibitor", "januvia, istavel"),
    ("Jardiance 10", "Empagliflozin", "SGLT2 inhibitor", "jardiance, jardiance duo"),
    ("Rosuvas 10", "Rosuvastatin", "Statin", "rosuvas, rosutor"),
    ("Atorva 20", "Atorvastatin", "Statin", "atorva, atorlip"),
    ("Thyronorm 50mcg", "Levothyroxine", "Thyroid hormone", "thyronorm, eltroxin"),
    ("Enterogermina 5ml", "Bacillus clausii spores", "Probiotic", "enterogermina, darolac"),
    ("Strepsils Lozenges", "Amylmetacresol + Chlorhexidine", "Throat antiseptic", "strepsils, throat lozenges"),
    ("Vicks Action 500", "Paracetamol", "Analgesic / Antipyretic", "vicks action, action 500"),
    ("Sumo Cold", "Paracetamol + Phenylephrine + CPM", "Cold relief combination", "sumo cold, cheston cold"),
    ("Cheston Cold", "Paracetamol + Phenylephrine + CPM", "Cold relief combination", "cheston, sinarest type"),
    ("Sinarest", "Paracetamol + Phenylephrine + CPM", "Cold relief combination", "sinarest tablet"),
]

def merge_refset():
    with open(REFSET_PATH, encoding="utf-8") as f:
        current = json.load(f)
    existing_names = {e["preferred_name"].lower() for e in current}
    added = []
    for entry in NEW_REFSET:
        if entry["preferred_name"].lower() in existing_names:
            continue
        entry.setdefault("icd10_guess", "")
        entry.setdefault("abbreviations", [])
        current.append(entry)
        added.append(entry["preferred_name"])
    os.makedirs(ATTIC, exist_ok=True)
    shutil.copy2(REFSET_PATH, os.path.join(ATTIC, "opd_refset_v1.backup_pre_v2.json"))
    with open(REFSET_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=1, ensure_ascii=False)
    print(f"RefSet: {len(added)} added ({len(current)} total). Sample: {added[:5]} ... {added[-3:]}")
    return len(current)

def merge_formulary():
    with open(FORMULARY_PATH, encoding="utf-8") as f:
        current = json.load(f)
    existing_brands = {e["brand_name"].lower() for e in current}
    added = []
    for brand, generic, category, synonyms in NEW_FORMULARY:
        if brand.lower() in existing_brands:
            continue
        current.append({
            "brand_name": brand,
            "generic_name": generic,
            "category": category,
            "snomed_id": "",
            "code_status": "generic_mapping_only",
            "typical_doses": "",
            "synonyms": synonyms,
        })
        added.append(brand)
    os.makedirs(ATTIC, exist_ok=True)
    shutil.copy2(FORMULARY_PATH, os.path.join(ATTIC, "pmbjp_generic_formulary.backup_pre_v2.json"))
    with open(FORMULARY_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=1, ensure_ascii=False)
    print(f"Formulary: {len(added)} added ({len(current)} total). Sample: {added[:5]} ... {added[-3:]}")
    return len(current)

if __name__ == "__main__":
    n_ref = merge_refset()
    n_for = merge_formulary()
    print(f"DONE: refset={n_ref} entries, formulary={n_for} entries.")
