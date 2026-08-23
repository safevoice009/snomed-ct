"""
build_clinical_db.py
Creates and populates the SQLite FTS5 database (clinical_knowledge.db)
with real-world Indian pharmaceutical brand-to-generic mappings,
SNOMED CT clinical findings, disorders, procedures, and LOINC observation codes.
"""

import os
import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_clinical_db")

# Top Indian Pharmaceutical Brand-to-Generic Mappings with SNOMED CT SCTIDs
INDIAN_BRAND_MEDICATIONS = [
    # Antibiotics & Anti-infectives
    {
        "brand_name": "Augmentin",
        "generic_name": "Amoxicillin and clavulanic acid",
        "category": "Antibiotic (Penicillin + Beta-lactamase inhibitor)",
        "snomed_id": "372687004",
        "typical_doses": ["625mg", "1000mg", "375mg"],
        "synonyms": ["augmentin", "augmentin 625", "augmentin 625 duo", "moxclav", "moxikind-cv", "clavum 625", "amoxyclav"]
    },
    {
        "brand_name": "Azee",
        "generic_name": "Azithromycin",
        "category": "Macrolide Antibiotic",
        "snomed_id": "387525002",
        "typical_doses": ["250mg", "500mg"],
        "synonyms": ["azee", "azee 500", "azithral", "zithrox", "aziwok", "azimax"]
    },
    {
        "brand_name": "Cifran",
        "generic_name": "Ciprofloxacin",
        "category": "Fluoroquinolone Antibiotic",
        "snomed_id": "387508007",
        "typical_doses": ["250mg", "500mg"],
        "synonyms": ["cifran", "cifran 500", "ciplox", "ciprobid", "alcipro"]
    },
    {
        "brand_name": "Taxim-O",
        "generic_name": "Cefixime",
        "category": "Cephalosporin Antibiotic (3rd Gen)",
        "snomed_id": "372833008",
        "typical_doses": ["100mg", "200mg"],
        "synonyms": ["taxim o", "taxim-o", "cefix", "zifi", "mahacef", "cefolac"]
    },
    {
        "brand_name": "Monocef",
        "generic_name": "Ceftriaxone",
        "category": "Cephalosporin Antibiotic (Injectable)",
        "snomed_id": "387431003",
        "typical_doses": ["500mg", "1g", "2g"],
        "synonyms": ["monocef", "monocef 1g", "oframax", "xone", "ceftriaxone"]
    },
    {
        "brand_name": "Flagyl",
        "generic_name": "Metronidazole",
        "category": "Nitroimidazole / Antiprotozoal",
        "snomed_id": "387403001",
        "typical_doses": ["200mg", "400mg"],
        "synonyms": ["flagyl", "flagyl 400", "metrogyl", "metrogyl 400", "aristogyl"]
    },

    # Analgesics, Antipyretics & NSAIDs
    {
        "brand_name": "Dolo 650",
        "generic_name": "Paracetamol",
        "category": "Analgesic / Antipyretic",
        "snomed_id": "387517004",
        "typical_doses": ["500mg", "650mg"],
        "synonyms": ["dolo", "dolo 650", "calpol", "calpol 650", "crocin", "crocin 650", "pacimol", "paracetamol"]
    },
    {
        "brand_name": "Combiflam",
        "generic_name": "Ibuprofen and paracetamol",
        "category": "NSAID + Analgesic Combination",
        "snomed_id": "387207008",
        "typical_doses": ["400mg/325mg"],
        "synonyms": ["combiflam", "combiflam plus", "ibuprofen plus paracetamol", "brufen plus"]
    },
    {
        "brand_name": "Voveran",
        "generic_name": "Diclofenac",
        "category": "NSAID",
        "snomed_id": "387494007",
        "typical_doses": ["50mg", "75mg", "100mg SR"],
        "synonyms": ["voveran", "voveran 50", "voveran sr", "nac", "dynapar", "diclogesic", "diclofenac"]
    },
    {
        "brand_name": "Zerodol-SP",
        "generic_name": "Aceclofenac, paracetamol and serratiopeptidase",
        "category": "Triple NSAID Anti-inflammatory",
        "snomed_id": "387494007", # Aceclofenac class
        "typical_doses": ["100mg/325mg/15mg"],
        "synonyms": ["zerodol sp", "zerodol-sp", "hifenac-sp", "aceclo-sp", "dolokind-sp"]
    },
    {
        "brand_name": "Ultracet",
        "generic_name": "Tramadol and paracetamol",
        "category": "Opioid + Analgesic",
        "snomed_id": "387173000",
        "typical_doses": ["37.5mg/325mg"],
        "synonyms": ["ultracet", "tramazac plus", "dolzero", "tramadol plus paracetamol"]
    },

    # Gastrointestinal & Antacids / PPIs
    {
        "brand_name": "Pan-D",
        "generic_name": "Pantoprazole and domperidone",
        "category": "Proton Pump Inhibitor + Prokinetic",
        "snomed_id": "715879001",
        "typical_doses": ["40mg/30mg"],
        "synonyms": ["pan d", "pan-d", "pantocid-d", "pantodac-dsr", "penta-d", "pantop-d"]
    },
    {
        "brand_name": "Pan 40",
        "generic_name": "Pantoprazole",
        "category": "Proton Pump Inhibitor",
        "snomed_id": "387391007",
        "typical_doses": ["20mg", "40mg"],
        "synonyms": ["pan 40", "pan40", "pantocid", "pantodac", "pantop 40", "pantoprazole"]
    },
    {
        "brand_name": "Omez-D",
        "generic_name": "Omeprazole and domperidone",
        "category": "PPI + Prokinetic",
        "snomed_id": "387391007",
        "typical_doses": ["20mg/10mg"],
        "synonyms": ["omez d", "omez-d", "omez", "omez 20", "omeprazole"]
    },
    {
        "brand_name": "Razo-D",
        "generic_name": "Rabeprazole and domperidone",
        "category": "PPI + Prokinetic",
        "snomed_id": "387391007",
        "typical_doses": ["20mg/30mg"],
        "synonyms": ["razo d", "razo-d", "rabicip-d", "rabekind-dsr", "rabicip"]
    },
    {
        "brand_name": "Eldoper",
        "generic_name": "Loperamide",
        "category": "Antidiarrheal",
        "snomed_id": "387406009",
        "typical_doses": ["2mg"],
        "synonyms": ["eldoper", "lopamide", "imodium", "loperamide"]
    },
    {
        "brand_name": "Econorm",
        "generic_name": "Saccharomyces boulardii",
        "category": "Probiotic",
        "snomed_id": "715879001",
        "typical_doses": ["250mg", "sachet"],
        "synonyms": ["econorm", "darolac", "enterogermina", "sporlac", "probiotic"]
    },

    # Respiratory, Antiallergic & Cough
    {
        "brand_name": "Levocet-M",
        "generic_name": "Levocetirizine and montelukast",
        "category": "Antihistamine + Leukotriene Receptor Antagonist",
        "snomed_id": "715879001",
        "typical_doses": ["5mg/10mg"],
        "synonyms": ["levocet m", "levocet-m", "montair lc", "montair-lc", "monticope", "telekast-l", "montek-lc"]
    },
    {
        "brand_name": "Ascoril-D",
        "generic_name": "Dextromethorphan, phenylephrine and chlorpheniramine",
        "category": "Cough Suppressant + Decongestant",
        "snomed_id": "387207008",
        "typical_doses": ["100ml syrup", "5ml TDS"],
        "synonyms": ["ascoril d", "ascoril-d", "ascoril", "grilinctus", "benadryl dr", "tussq"]
    },
    {
        "brand_name": "Asthalin",
        "generic_name": "Salbutamol",
        "category": "Short-acting Beta2 Agonist (Bronchodilator)",
        "snomed_id": "387340003",
        "typical_doses": ["2mg", "4mg", "100mcg inhaler", "respules"],
        "synonyms": ["asthalin", "asthalin inhaler", "ventorlin", "salbair", "salbutamol"]
    },
    {
        "brand_name": "Budecort",
        "generic_name": "Budesonide",
        "category": "Inhaled Corticosteroid",
        "snomed_id": "387340003",
        "typical_doses": ["100mcg", "200mcg", "0.5mg respule"],
        "synonyms": ["budecort", "budecort inhaler", "budecort respules", "foracort", "pulmicort", "budesonide"]
    },

    # Cardiovascular & Antihypertensive
    {
        "brand_name": "Telma 40",
        "generic_name": "Telmisartan",
        "category": "Angiotensin II Receptor Blocker (ARB)",
        "snomed_id": "387532007",
        "typical_doses": ["20mg", "40mg", "80mg"],
        "synonyms": ["telma", "telma 40", "telma 80", "telmikind", "telvas", "telsartan", "telmisartan"]
    },
    {
        "brand_name": "Telma-AM",
        "generic_name": "Telmisartan and amlodipine",
        "category": "ARB + Calcium Channel Blocker Combination",
        "snomed_id": "387532007",
        "typical_doses": ["40mg/5mg", "80mg/5mg"],
        "synonyms": ["telma am", "telma-am", "telmikind-am", "telsartan-am", "amlong-tl", "telista-am"]
    },
    {
        "brand_name": "Amlong",
        "generic_name": "Amlodipine",
        "category": "Calcium Channel Blocker",
        "snomed_id": "387532007",
        "typical_doses": ["2.5mg", "5mg", "10mg"],
        "synonyms": ["amlong", "amlong 5", "stamlo", "amlovas", "amlodac", "amlodipine"]
    },
    {
        "brand_name": "Envas",
        "generic_name": "Enalapril",
        "category": "ACE Inhibitor",
        "snomed_id": "387532007",
        "typical_doses": ["2.5mg", "5mg", "10mg"],
        "synonyms": ["envas", "envas 5", "nuril", "enam", "enalapril"]
    },
    {
        "brand_name": "Ecosprin",
        "generic_name": "Aspirin (Acetylsalicylic acid)",
        "category": "Antiplatelet / Salicylate",
        "snomed_id": "387458008",
        "typical_doses": ["75mg", "150mg"],
        "synonyms": ["ecosprin", "ecosprin 75", "ecosprin 150", "aspirin", "asa", "delisprin", "disprin"]
    },
    {
        "brand_name": "Clopilet",
        "generic_name": "Clopidogrel",
        "category": "Antiplatelet (P2Y12 Inhibitor)",
        "snomed_id": "387458008",
        "typical_doses": ["75mg"],
        "synonyms": ["clopilet", "clopilet 75", "deplatt", "plavix", "clopidogrel", "clopivas"]
    },
    {
        "brand_name": "Atorva",
        "generic_name": "Atorvastatin",
        "category": "HMG-CoA Reductase Inhibitor (Statin)",
        "snomed_id": "387584000",
        "typical_doses": ["10mg", "20mg", "40mg"],
        "synonyms": ["atorva", "atorva 10", "atorva 20", "atorlip", "lipicure", "tonact", "atorvastatin"]
    },
    {
        "brand_name": "Rozavel",
        "generic_name": "Rosuvastatin",
        "category": "Statin",
        "snomed_id": "387584000",
        "typical_doses": ["5mg", "10mg", "20mg"],
        "synonyms": ["rozavel", "rozavel 10", "rosuvas", "rosave", "crestor", "rosuvastatin"]
    },

    # Endocrine & Diabetes
    {
        "brand_name": "Glycomet",
        "generic_name": "Metformin",
        "category": "Biguanide Antidiabetic",
        "snomed_id": "386864001",
        "typical_doses": ["500mg", "850mg", "1000mg SR"],
        "synonyms": ["glycomet", "glycomet 500", "glycomet sr", "glyciphage", "obimet", "gluformin", "metformin"]
    },
    {
        "brand_name": "Glycomet-GP",
        "generic_name": "Glimepiride and metformin",
        "category": "Sulfonylurea + Biguanide Combination",
        "snomed_id": "386864001",
        "typical_doses": ["1mg/500mg", "2mg/500mg"],
        "synonyms": ["glycomet gp", "glycomet-gp", "glyciphage-g", "amaryl-m", "glimy-m", "gluconorm-g"]
    },
    {
        "brand_name": "Januvia",
        "generic_name": "Sitagliptin",
        "category": "DPP-4 Inhibitor",
        "snomed_id": "386864001",
        "typical_doses": ["50mg", "100mg"],
        "synonyms": ["januvia", "janumet", "istavel", "sitagliptin", "zita"]
    },
    {
        "brand_name": "Forxiga",
        "generic_name": "Dapagliflozin",
        "category": "SGLT2 Inhibitor",
        "snomed_id": "386864001",
        "typical_doses": ["5mg", "10mg"],
        "synonyms": ["forxiga", "forxiga 10", "dapa", "oxra", "dapaglyn", "dapagliflozin"]
    },
    {
        "brand_name": "Thyronorm",
        "generic_name": "Levothyroxine sodium",
        "category": "Thyroid Hormone",
        "snomed_id": "387439001",
        "typical_doses": ["25mcg", "50mcg", "75mcg", "100mcg", "125mcg"],
        "synonyms": ["thyronorm", "thyronorm 50", "thyronorm 100", "eltroxin", "thyrox", "levothyroxine"]
    },

    # Vitamins, Minerals & Supplements
    {
        "brand_name": "Shelcal 500",
        "generic_name": "Calcium and vitamin D3",
        "category": "Mineral & Vitamin Supplement",
        "snomed_id": "715879001",
        "typical_doses": ["500mg/250IU"],
        "synonyms": ["shelcal", "shelcal 500", "shelcal hd", "cipcal", "gemcal", "calcium"]
    },
    {
        "brand_name": "Becosules",
        "generic_name": "B-complex with vitamin C",
        "category": "Vitamin Complex",
        "snomed_id": "715879001",
        "typical_doses": ["capsule OD"],
        "synonyms": ["becosules", "becosules z", "cobadex czs", "b-complex", "neurobion forte"]
    },
    {
        "brand_name": "Supradyn",
        "generic_name": "Multivitamins and minerals",
        "category": "Multivitamin",
        "snomed_id": "715879001",
        "typical_doses": ["daily tablet"],
        "synonyms": ["supradyn", "zincovit", "a to z", "revital", "multivitamin"]
    },
    {
        "brand_name": "Folvite",
        "generic_name": "Folic acid",
        "category": "Vitamin B9",
        "snomed_id": "387439001",
        "typical_doses": ["5mg"],
        "synonyms": ["folvite", "folvite 5mg", "folic acid", "folinext"]
    },
    {
        "brand_name": "Orofer-XT",
        "generic_name": "Ferrous ascorbate and folic acid",
        "category": "Hematinic (Iron Supplement)",
        "snomed_id": "387439001",
        "typical_doses": ["100mg/1.5mg"],
        "synonyms": ["orofer", "orofer xt", "orofer-xt", "autrin", "feronia-xt", "iron tablet"]
    }
]

# Standard SNOMED CT Clinical Findings, Symptoms and Disorders
SNOMED_CLINICAL_CONCEPTS = [
    {
        "concept_id": "25064002",
        "preferred_name": "Headache (finding)",
        "semantic_tag": "finding",
        "synonyms": ["headache", "head ache", "sar dard", "sar dard ho raha hai", "sar dard tha", "sir dard", "cephalea"]
    },
    {
        "concept_id": "62315008",
        "preferred_name": "Diarrhoea (finding)",
        "semantic_tag": "finding",
        "synonyms": ["diarrhea", "diarrhoea", "loose motion", "loose motions", "pet kharab", "pet kharab hai", "dast", "watery stools"]
    },
    {
        "concept_id": "49727002",
        "preferred_name": "Cough (finding)",
        "semantic_tag": "finding",
        "synonyms": ["cough", "khansi", "dry cough", "severe khansi", "productive cough", "coughing", "kali khansi"]
    },
    {
        "concept_id": "23924001",
        "preferred_name": "Chest tightness (finding)",
        "semantic_tag": "finding",
        "synonyms": ["chest tightness", "tightness in chest", "chest heaviness", "chest congestion", "seene me jakdan"]
    },
    {
        "concept_id": "61582004",
        "preferred_name": "Allergic rhinitis (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["allergic rhinitis", "rhinitis", "sardi", "sneezing", "cheenk", "runny nose", "nazla"]
    },
    {
        "concept_id": "38341003",
        "preferred_name": "Hypertension (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["hypertension", "HTN", "high blood pressure", "high BP", "BP high", "ucch raktchap"]
    },
    {
        "concept_id": "386661006",
        "preferred_name": "Fever (finding)",
        "semantic_tag": "finding",
        "synonyms": ["fever", "bukhar", "pyrexia", "taap", "elevated temperature", "101F", "102F", "103F", "febrile"]
    },
    {
        "concept_id": "443681002",
        "preferred_name": "Acute gastroenteritis (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["acute gastroenteritis", "AGE", "gastroenteritis", "infective diarrhea", "stomach flu"]
    },
    {
        "concept_id": "73211009",
        "preferred_name": "Diabetes mellitus (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["diabetes mellitus", "diabetes", "DM", "T2DM", "sugar", "high sugar", "madhumeha"]
    },
    {
        "concept_id": "60845006",
        "preferred_name": "Dyspnea on exertion (finding)",
        "semantic_tag": "finding",
        "synonyms": ["SOBOE", "shortness of breath on exertion", "dyspnea on exertion", "breathlessness on walking", "dam fulna"]
    },
    {
        "concept_id": "30711000",
        "preferred_name": "Edema of foot (finding)",
        "semantic_tag": "finding",
        "synonyms": ["pedal edema", "pedal edema +", "foot swelling", "swelling in feet", "pair me sujan"]
    },
    {
        "concept_id": "21522001",
        "preferred_name": "Abdominal pain (finding)",
        "semantic_tag": "finding",
        "synonyms": ["abdominal pain", "abd pain", "stomach ache", "pet dard", "pet me dard", "cramps"]
    },
    {
        "concept_id": "422587007",
        "preferred_name": "Nausea (finding)",
        "semantic_tag": "finding",
        "synonyms": ["nausea", "nauseous", "ji machlana", "ulti jaisa lagna", "queasiness"]
    },
    {
        "concept_id": "422400008",
        "preferred_name": "Vomiting (finding)",
        "semantic_tag": "finding",
        "synonyms": ["vomiting", "vomit", "ulti", "emesis"]
    },
    {
        "concept_id": "267036007",
        "preferred_name": "Dyspnea (finding)",
        "semantic_tag": "finding",
        "synonyms": ["dyspnea", "shortness of breath", "SOB", "breathlessness", "saans lene me taklif"]
    },
    {
        "concept_id": "195967001",
        "preferred_name": "Asthma (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["asthma", "bronchial asthma", "dama", "wheezing disorder"]
    },
    {
        "concept_id": "10509002",
        "preferred_name": "Acute bronchitis (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["acute bronchitis", "bronchitis", "chest infection"]
    },
    {
        "concept_id": "233604007",
        "preferred_name": "Pneumonia (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["pneumonia", "lung consolidation", "chest pneumonia"]
    },
    {
        "concept_id": "36971009",
        "preferred_name": "Sinusitis (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["sinusitis", "sinus infection", "sinus pain", "sinus headache"]
    },
    {
        "concept_id": "162059005",
        "preferred_name": "Sore throat (finding)",
        "semantic_tag": "finding",
        "synonyms": ["sore throat", "throat pain", "gala kharab", "gale me dard", "pharyngitis"]
    },
    {
        "concept_id": "840539006",
        "preferred_name": "COVID-19 (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["covid 19", "covid-19", "coronavirus", "sars-cov-2"]
    },
    {
        "concept_id": "38362002",
        "preferred_name": "Dengue fever (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["dengue", "dengue fever", "breakbone fever"]
    },
    {
        "concept_id": "61462000",
        "preferred_name": "Malaria (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["malaria", "plasmodium vivax", "plasmodium falciparum"]
    },
    {
        "concept_id": "4834000",
        "preferred_name": "Typhoid fever (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["typhoid", "typhoid fever", "enteric fever"]
    },
    {
        "concept_id": "271737000",
        "preferred_name": "Anemia (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["anemia", "anaemia", "low hemoglobin", "khoon ki kami", "iron deficiency"]
    },
    {
        "concept_id": "14304000",
        "preferred_name": "Hypothyroidism (disorder)",
        "semantic_tag": "disorder",
        "synonyms": ["hypothyroidism", "underactive thyroid", "thyroid problem", "high TSH"]
    }
]

# Standard LOINC Codes for Observations / Lab Tests
LOINC_CODES = [
    {"loinc_code": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg"},
    {"loinc_code": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg"},
    {"loinc_code": "8867-4", "display": "Heart rate", "unit": "/min"},
    {"loinc_code": "8310-5", "display": "Body temperature", "unit": "Cel"},
    {"loinc_code": "2708-6", "display": "Oxygen saturation in Arterial blood", "unit": "%"},
    {"loinc_code": "29463-7", "display": "Body weight", "unit": "kg"},
    {"loinc_code": "8302-2", "display": "Body height", "unit": "cm"},
    {"loinc_code": "15074-8", "display": "Glucose [Moles/volume] in Blood", "unit": "mg/dL"},
    {"loinc_code": "4548-4", "display": "Hemoglobin A1c/Hemoglobin.total in Blood", "unit": "%"}
]

def init_clinical_db(db_path: str = "clinical_knowledge.db"):
    """Creates tables and indexes in SQLite FTS5 database."""
    logger.info(f"Initializing SQLite Clinical Knowledge Database at {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Drop existing tables if rebuilding
    cur.execute("DROP TABLE IF EXISTS concepts")
    cur.execute("DROP TABLE IF EXISTS concepts_fts")
    cur.execute("DROP TABLE IF EXISTS brands")
    cur.execute("DROP TABLE IF EXISTS brands_fts")
    cur.execute("DROP TABLE IF EXISTS loinc_observations")
    
    # 1. Concepts Master Table
    cur.execute("""
        CREATE TABLE concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id TEXT UNIQUE NOT NULL,
            preferred_name TEXT NOT NULL,
            semantic_tag TEXT NOT NULL,
            synonyms_json TEXT NOT NULL
        )
    """)
    
    # 2. Concepts FTS5 Virtual Table
    cur.execute("""
        CREATE VIRTUAL TABLE concepts_fts USING fts5(
            concept_id UNINDEXED,
            preferred_name,
            semantic_tag UNINDEXED,
            synonyms
        )
    """)
    
    # 3. Brands Master Table
    cur.execute("""
        CREATE TABLE brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            generic_name TEXT NOT NULL,
            category TEXT NOT NULL,
            snomed_id TEXT NOT NULL,
            typical_doses_json TEXT NOT NULL,
            synonyms_json TEXT NOT NULL
        )
    """)
    
    # 4. Brands FTS5 Virtual Table
    cur.execute("""
        CREATE VIRTUAL TABLE brands_fts USING fts5(
            brand_name,
            generic_name,
            category,
            snomed_id UNINDEXED,
            synonyms
        )
    """)
    
    # 5. LOINC Observations Table
    cur.execute("""
        CREATE TABLE loinc_observations (
            loinc_code TEXT PRIMARY KEY,
            display TEXT NOT NULL,
            unit TEXT NOT NULL
        )
    """)
    
    # Populate Concepts
    for c in SNOMED_CLINICAL_CONCEPTS:
        syn_str = ", ".join(c["synonyms"])
        cur.execute(
            "INSERT INTO concepts (concept_id, preferred_name, semantic_tag, synonyms_json) VALUES (?, ?, ?, ?)",
            (c["concept_id"], c["preferred_name"], c["semantic_tag"], json.dumps(c["synonyms"]))
        )
        cur.execute(
            "INSERT INTO concepts_fts (concept_id, preferred_name, semantic_tag, synonyms) VALUES (?, ?, ?, ?)",
            (c["concept_id"], c["preferred_name"], c["semantic_tag"], syn_str)
        )
        
    # Populate Indian Pharma Brands
    for b in INDIAN_BRAND_MEDICATIONS:
        syn_str = ", ".join(b["synonyms"])
        cur.execute(
            "INSERT INTO brands (brand_name, generic_name, category, snomed_id, typical_doses_json, synonyms_json) VALUES (?, ?, ?, ?, ?, ?)",
            (b["brand_name"], b["generic_name"], b["category"], b["snomed_id"], json.dumps(b["typical_doses"]), json.dumps(b["synonyms"]))
        )
        cur.execute(
            "INSERT INTO brands_fts (brand_name, generic_name, category, snomed_id, synonyms) VALUES (?, ?, ?, ?, ?)",
            (b["brand_name"], b["generic_name"], b["category"], b["snomed_id"], syn_str)
        )
        
    # Populate LOINC
    for l in LOINC_CODES:
        cur.execute(
            "INSERT INTO loinc_observations (loinc_code, display, unit) VALUES (?, ?, ?)",
            (l["loinc_code"], l["display"], l["unit"])
        )
        
    conn.commit()
    conn.close()
    logger.info("Successfully populated clinical_knowledge.db with SNOMED, LOINC, and Indian Drug mappings!")

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinical_knowledge.db")
    init_clinical_db(db_file)
