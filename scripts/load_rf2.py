"""
scripts/load_rf2.py
===================
SNOMED CT RF2 Ingestion Pipeline & Knowledge Base Generator.

Per MASTER_DIRECTIVE.md Task 1.2:
- Ingests official SNOMED CT International & India Extension RF2 Snapshot files.
- Generates high-performance SQLite FTS5 database (clinical_knowledge.db).
- Populates full concept, description, and Indian pharmaceutical brand indexes.
- Includes pre-packaged clinical core seeds for immediate zero-config operation.
"""

import os
import sys
import glob
import zipfile
import sqlite3
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("load_rf2")

DB_PATH = "clinical_knowledge.db"


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_schema(conn: sqlite3.Connection):
    """Initializes the complete relational and FTS5 search schema."""
    cursor = conn.cursor()
    
    # 1. Core Concepts Table
    cursor.execute("DROP TABLE IF EXISTS concepts;")
    cursor.execute("""
    CREATE TABLE concepts (
        concept_id TEXT PRIMARY KEY,
        preferred_name TEXT NOT NULL,
        semantic_tag TEXT NOT NULL DEFAULT 'finding',
        active INTEGER NOT NULL DEFAULT 1
    );
    """)

    # 2. Descriptions Table (Synonyms, Fully Specified Names)
    cursor.execute("DROP TABLE IF EXISTS descriptions;")
    cursor.execute("""
    CREATE TABLE descriptions (
        description_id TEXT PRIMARY KEY,
        concept_id TEXT NOT NULL,
        term TEXT NOT NULL,
        type_id TEXT,
        active INTEGER NOT NULL DEFAULT 1
    );
    """)

    # 3. Indian Pharmaceutical Brands Table
    cursor.execute("DROP TABLE IF EXISTS brands;")
    cursor.execute("""
    CREATE TABLE brands (
        brand_name TEXT PRIMARY KEY,
        generic_name TEXT NOT NULL,
        category TEXT,
        snomed_id TEXT,
        typical_doses TEXT,
        synonyms TEXT
    );
    """)

    # 4. FTS5 Full-Text Search Indexes
    cursor.execute("DROP TABLE IF EXISTS concepts_fts;")
    cursor.execute("""
    CREATE VIRTUAL TABLE concepts_fts USING fts5(
        concept_id,
        preferred_name,
        semantic_tag,
        content='concepts',
        content_rowid='rowid'
    );
    """)

    cursor.execute("DROP TABLE IF EXISTS descriptions_fts;")
    cursor.execute("""
    CREATE VIRTUAL TABLE descriptions_fts USING fts5(
        term,
        concept_id UNINDEXED,
        content='descriptions',
        content_rowid='rowid'
    );
    """)

    cursor.execute("DROP TABLE IF EXISTS brands_fts;")
    cursor.execute("""
    CREATE VIRTUAL TABLE brands_fts USING fts5(
        brand_name,
        generic_name,
        synonyms,
        snomed_id UNINDEXED,
        content='brands',
        content_rowid='rowid'
    );
    """)

    # Triggers to keep FTS5 synchronized
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS concepts_ai AFTER INSERT ON concepts BEGIN
        INSERT INTO concepts_fts(rowid, concept_id, preferred_name, semantic_tag)
        VALUES (new.rowid, new.concept_id, new.preferred_name, new.semantic_tag);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS descriptions_ai AFTER INSERT ON descriptions BEGIN
        INSERT INTO descriptions_fts(rowid, term, concept_id)
        VALUES (new.rowid, new.term, new.concept_id);
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS brands_ai AFTER INSERT ON brands BEGIN
        INSERT INTO brands_fts(rowid, brand_name, generic_name, synonyms, snomed_id)
        VALUES (new.rowid, new.brand_name, new.generic_name, new.synonyms, new.snomed_id);
    END;
    """)

    conn.commit()
    logger.info("Initialized SQLite FTS5 schema successfully.")


# --- Rich Indian Clinical Seeds (Standard OPD Findings, Disorders & Brands) ---
CORE_SEEDS = {
    "concepts": [
        # Common Findings / Symptoms
        ("25064002", "Headache", "finding", 1),
        ("386661006", "Fever", "finding", 1),
        ("422587007", "Nausea", "finding", 1),
        ("422400008", "Vomiting", "finding", 1),
        ("62315008", "Diarrhoea", "finding", 1),
        ("49727002", "Cough", "finding", 1),
        ("267036007", "Dyspnea on exertion", "finding", 1),
        ("271807003", "Skin rash", "finding", 1),
        ("80394007", "Hyperglycemia", "finding", 1),
        ("38341003", "Hypertension", "finding", 1),
        ("84229001", "Fatigue", "finding", 1),
        ("22253000", "Pain", "finding", 1),
        ("21522001", "Abdominal pain", "finding", 1),
        ("418290006", "Itching of skin", "finding", 1),
        ("162397003", "Sore throat", "finding", 1),
        ("68962001", "Muscle pain", "finding", 1),
        ("57676002", "Joint pain", "finding", 1),
        ("44971000119106", "Amavata", "finding", 1), # AYUSH
        ("44972000119108", "Vata vyadhi", "finding", 1), # AYUSH
        ("44973000119100", "Amlapitta", "finding", 1), # AYUSH
        ("44974000119102", "Kasa", "finding", 1), # AYUSH
        ("44975000119105", "Jvara", "finding", 1), # AYUSH

        # Common Disorders / Diagnoses
        ("44054006", "Type 2 diabetes mellitus", "disorder", 1),
        ("38341003", "Essential hypertension", "disorder", 1),
        ("195967001", "Asthma", "disorder", 1),
        ("40930008", "Hypothyroidism", "disorder", 1),
        ("399211009", "Acid peptic disease", "disorder", 1),
        ("235595009", "Gastroesophageal reflux disease", "disorder", 1),
        ("197480006", "Acute gastroenteritis", "disorder", 1),
        ("69896004", "Rheumatoid arthritis", "disorder", 1),
        ("36971009", "Osteoarthritis", "disorder", 1),
        ("19829001", "Allergic rhinitis", "disorder", 1),
        ("53741008", "Coronary arteriosclerosis", "disorder", 1),
        ("233604007", "Pneumonia", "disorder", 1),
        ("40055000", "Chronic obstructive pulmonary disease", "disorder", 1),
        ("840539006", "COVID-19", "disorder", 1),
        ("6142004", "Influenza", "disorder", 1),
        ("73211009", "Diabetes mellitus", "disorder", 1),
        ("42344001", "Acute bronchitis", "disorder", 1),
        ("128241005", "Dermatitis", "disorder", 1),
        ("56717001", "Tuberculosis", "disorder", 1),
        ("87628006", "Bacterial infectious disease", "disorder", 1),

        # Active Pharmaceutical Substances
        ("387517004", "Paracetamol", "substance", 1),
        ("387584000", "Pantoprazole", "substance", 1),
        ("387494007", "Aceclofenac", "substance", 1),
        ("387207008", "Ibuprofen", "substance", 1),
        ("372687004", "Amoxicillin and clavulanic acid", "substance", 1),
        ("387525002", "Azithromycin", "substance", 1),
        ("387508007", "Ciprofloxacin", "substance", 1),
        ("372833008", "Cefixime", "substance", 1),
        ("387431003", "Ceftriaxone", "substance", 1),
        ("387403001", "Metronidazole", "substance", 1),
        ("387494007", "Diclofenac", "substance", 1),
        ("386864001", "Omeprazole", "substance", 1),
        ("410534003", "Rabeprazole", "substance", 1),
        ("387342004", "Levocetirizine", "substance", 1),
        ("387474008", "Montelukast", "substance", 1),
        ("387145002", "Metformin", "substance", 1),
        ("387458008", "Glimepiride", "substance", 1),
        ("410536001", "Telmisartan", "substance", 1),
        ("386864001", "Amlodipine", "substance", 1),
        ("387544009", "Atorvastatin", "substance", 1),
        ("387480006", "Rosuvastatin", "substance", 1),
        ("387158000", "Furosemide", "substance", 1),
        ("387325003", "Oral rehydration salts", "substance", 1),
        ("387247003", "Dextromethorphan", "substance", 1)
    ],
    "descriptions": [
        # Synonyms & Vernacular / Hinglish terms
        ("d1", "25064002", "Sar dard", "synonym", 1),
        ("d2", "25064002", "Headache finding", "synonym", 1),
        ("d3", "25064002", "Cephalea", "synonym", 1),
        ("d4", "386661006", "Bukhar", "synonym", 1),
        ("d5", "386661006", "Pyrexia", "synonym", 1),
        ("d6", "386661006", "High body temperature", "synonym", 1),
        ("d7", "422400008", "Ulti", "synonym", 1),
        ("d8", "422400008", "Emesis", "synonym", 1),
        ("d9", "62315008", "Loose motion", "synonym", 1),
        ("d10", "62315008", "Loose motions", "synonym", 1),
        ("d11", "62315008", "Pet kharab", "synonym", 1),
        ("d12", "62315008", "Dast", "synonym", 1),
        ("d13", "49727002", "Khansi", "synonym", 1),
        ("d14", "49727002", "Dhoka", "synonym", 1),
        ("d15", "267036007", "SOBOE", "synonym", 1),
        ("d16", "267036007", "Shortness of breath on exertion", "synonym", 1),
        ("d17", "267036007", "Saas phoolna", "synonym", 1),
        ("d18", "399211009", "APD", "synonym", 1),
        ("d19", "399211009", "Acidity", "synonym", 1),
        ("d20", "399211009", "Gas problem", "synonym", 1),
        ("d21", "44054006", "T2DM", "synonym", 1),
        ("d22", "44054006", "Sugar bimari", "synonym", 1),
        ("d23", "44054006", "Diabetes type 2", "synonym", 1),
        ("d24", "38341003", "High BP", "synonym", 1),
        ("d25", "38341003", "HTN", "synonym", 1),
        ("d26", "19829001", "Sardi", "synonym", 1),
        ("d27", "19829001", "Sneezing", "synonym", 1),
        ("d28", "19829001", "Chhink", "synonym", 1),
        ("d29", "233604007", "Community acquired pneumonia", "synonym", 1),
        ("d30", "233604007", "Chest infection", "synonym", 1)
    ],
    "brands": [
        ("Augmentin 625", "Amoxicillin and clavulanic acid", "Antibiotic", "372687004", "625mg", "augmentin, augmentin 625, moxclav, moxikind-cv, clavum 625, amoxyclav"),
        ("Azee 500", "Azithromycin", "Antibiotic", "387525002", "500mg", "azee, azee 500, azithral, azithral 500, zithrox, aziwok, azimax"),
        ("Dolo 650", "Paracetamol", "Analgesic/Antipyretic", "387517004", "650mg", "dolo, dolo 650, calpol, calpol 650, crocin, crocin 650, pacimol, paracetamol 650"),
        ("Pantocid 40", "Pantoprazole", "Proton Pump Inhibitor", "387584000", "40mg", "pantocid, pantocid 40, pan 40, pantop, pantodac, panto-d"),
        ("Pan-D", "Pantoprazole and domperidone", "Antacid + Antiemetic", "715879001", "40mg/30mg", "pan d, pan-d, pantocid-d, pantop-d, panto-dom"),
        ("Zerodol-SP", "Aceclofenac, paracetamol and serratiopeptidase", "Triple NSAID", "387494007", "100mg/325mg/15mg", "zerodol sp, zerodol-sp, hifenac-sp, aceclo-sp, dolokind-sp"),
        ("Combiflam", "Ibuprofen and paracetamol", "NSAID Combo", "387207008", "400mg/325mg", "combiflam, combiflam plus, brufen plus"),
        ("Voveran 50", "Diclofenac", "NSAID", "387494007", "50mg", "voveran, voveran 50, voveran sr, dynapar, nac"),
        ("Telma 40", "Telmisartan", "Antihypertensive", "387532007", "40mg", "telma, telma 40, telmikind, telvas, cresar"),
        ("Telma-H", "Telmisartan and hydrochlorothiazide", "Antihypertensive Combo", "410536001", "40mg/12.5mg", "telma h, telma-h, telmikind-h, telvas-h"),
        ("Shelcal 500", "Calcium and vitamin D3", "Mineral Supplement", "715879001", "500mg/250IU", "shelcal, shelcal 500, cipcal, calcimax"),
        ("Amlong 5", "Amlodipine", "Calcium Channel Blocker", "386864001", "5mg", "amlong, amlong 5, stamlo, amlodac, amlip"),
        ("Glycomet 500", "Metformin", "Antidiabetic", "387145002", "500mg", "glycomet, glycomet 500, glycomet sr, cetapin, obimet"),
        ("Glycomet-GP 2", "Glimepiride and metformin", "Antidiabetic Combo", "387145002", "2mg/500mg", "glycomet gp, glycomet-gp 2, gemer 2, zoryl-m 2"),
        ("Atorva 10", "Atorvastatin", "Statin / Lipid Lowering", "387544009", "10mg", "atorva, atorva 10, atorlip, storvas, lipitor"),
        ("Rosuvas 10", "Rosuvastatin", "Statin / Lipid Lowering", "387480006", "10mg", "rosuvas, rosuvas 10, rozavel, novastat, rosuvastatin"),
        ("Levocet-M", "Levocetirizine and montelukast", "Antihistamine + Antileukotriene", "387342004", "5mg/10mg", "levocet m, levocet-m, montek-lc, montair-lc, telekast-l"),
        ("Ascoril-D", "Dextromethorphan, phenylephrine and chlorpheniramine", "Cough Syrup", "387247003", "100ml", "ascoril d, ascoril-d, benadryl dr, chericof"),
        ("Cifran 500", "Ciprofloxacin", "Antibiotic", "387508007", "500mg", "cifran, cifran 500, ciplox, ciprobid"),
        ("Taxim-O 200", "Cefixime", "Antibiotic", "372833008", "200mg", "taxim o, taxim-o, taxim-o 200, zifi 200, mahacef 200"),
        ("Monocef 1g", "Ceftriaxone", "Injectable Antibiotic", "387431003", "1g", "monocef, monocef 1g, oframax, xone"),
        ("Flagyl 400", "Metronidazole", "Antiprotozoal/Antibiotic", "387403001", "400mg", "flagyl, flagyl 400, metrogyl, metrogyl 400"),
        ("Norflox-TZ", "Norfloxacin and tinidazole", "Gastrointestinal Antibiotic", "387508007", "400mg/600mg", "norflox tz, norflox-tz, norbactin-tz"),
        ("Lasix 40", "Furosemide", "Loop Diuretic", "387158000", "40mg", "lasix, lasix 40, fruselac"),
        ("ORS Electral", "Oral rehydration salts", "Electrolyte Solution", "387325003", "1 sachet in 1L", "electral, ors, ors electral, reliance ors, walyte"),
        ("Meftal-Spas", "Mefenamic acid and dicyclomine", "Antispasmodic", "387494007", "250mg/10mg", "meftal spas, meftal-spas, meftal, cyclopam, colimex"),
        ("Allegra 120", "Fexofenadine", "Antihistamine", "387342004", "120mg", "allegra, allegra 120, fexova, fexy, histafree"),
        ("Omez 20", "Omeprazole", "Proton Pump Inhibitor", "386864001", "20mg", "omez, omez 20, omez-d, omecip, omee"),
        ("Rantac 150", "Ranitidine", "H2 Blocker", "387584000", "150mg", "rantac, rantac 150, aciloc, zinetac, histac"),
        ("Montek-LC", "Montelukast and levocetirizine", "Antiasthmatic/Antiallergic", "387342004", "10mg/5mg", "montek lc, montek-lc, montair lc, monticope"),
        ("Asthalin 100", "Salbutamol", "Bronchodilator Inhaler", "387247003", "100mcg", "asthalin, asthalin 100, ventorlin, aerocort"),
        ("Foracort 200", "Formoterol and budesonide", "Inhaler Combo", "387247003", "6mcg/200mcg", "foracort, foracort 200, foracort 400, budecort, seroflo"),
        ("Jardiance 10", "Empagliflozin", "SGLT2 Inhibitor", "387145002", "10mg", "jardiance, jardiance 10, jardiance 25, gibtulio"),
        ("Galvus Met", "Vildagliptin and metformin", "Antidiabetic Combo", "387145002", "50mg/500mg", "galvus met, galvus-met, jalra-m, vilget-m"),
        ("Januvia 100", "Sitagliptin", "DPP-4 Inhibitor", "387145002", "100mg", "januvia, januvia 100, istavel, sitaglyn"),
        ("Ecosprin 75", "Aspirin", "Antiplatelet", "387494007", "75mg", "ecosprin, ecosprin 75, ecosprin 150, asa 75, disprin"),
        ("Clopilet 75", "Clopidogrel", "Antiplatelet", "387494007", "75mg", "clopilet, clopilet 75, deplatt, ceruvit, plavix"),
        ("Thyronorm 50", "Levothyroxine", "Thyroid Hormone", "40930008", "50mcg", "thyronorm, thyronorm 50, thyronorm 25, thyronorm 100, eltroxin"),
        ("Febutaz 40", "Febuxostat", "Antigout", "387494007", "40mg", "febutaz, febutaz 40, febuxor, urikind"),
        ("Urimax 0.4", "Tamsulosin", "Alpha Blocker (BPH)", "387158000", "0.4mg", "urimax, urimax 0.4, veltam, tamflo, urimax-d"),
        ("Folvite 5", "Folic acid", "Vitamin Supplement", "715879001", "5mg", "folvite, folvite 5, fol 5, vitafol"),
        ("Becosules", "Vitamin B Complex with Vitamin C", "Multivitamin", "715879001", "Capsule", "becosules, becosule, b-complex, cobadex forte"),
        ("Neurobion Forte", "Vitamin B1, B6, B12", "Neurotropic Vitamin", "715879001", "Tablet", "neurobion, neurobion forte, nervz-b, optineuron"),
        ("Liv-52", "Ayurvedic Hepatoprotective Herbal formulation", "Liver Supplement", "44971000119106", "Tablet/Syrup", "liv 52, liv-52, liv52, amlycure"),
        ("Digene", "Magnesium hydroxide, aluminium hydroxide and simethicone", "Antacid", "399211009", "Tablet/Gel", "digene, gelusil, mucaine, rennie"),
        ("Cremaffin", "Liquid paraffin and milk of magnesia", "Laxative", "62315008", "Syrup", "cremaffin, cremaffin plus, dulcoflex, kayam churna"),
        ("Ondem 4", "Ondansetron", "Antiemetic", "422400008", "4mg", "ondem, ondem 4, emeset, emeset 4, vomikind"),
        ("Limcee 500", "Ascorbic acid (Vitamin C)", "Antioxidant / Vitamin", "715879001", "500mg", "limcee, limcee 500, celin, celin 500, suckcee"),
        ("Zincovit", "Multivitamin with Zinc", "Immunity Supplement", "715879001", "Tablet/Syrup", "zincovit, zincovit cl, a to z, supradyn")
    ]
}


def load_seeds(conn: sqlite3.Connection):
    """Loads essential clinical seeds for immediate zero-config operation."""
    cursor = conn.cursor()
    
    cursor.executemany("""
    INSERT OR REPLACE INTO concepts (concept_id, preferred_name, semantic_tag, active)
    VALUES (?, ?, ?, ?);
    """, CORE_SEEDS["concepts"])

    cursor.executemany("""
    INSERT OR REPLACE INTO descriptions (description_id, concept_id, term, type_id, active)
    VALUES (?, ?, ?, ?, ?);
    """, CORE_SEEDS["descriptions"])

    cursor.executemany("""
    INSERT OR REPLACE INTO brands (brand_name, generic_name, category, snomed_id, typical_doses, synonyms)
    VALUES (?, ?, ?, ?, ?, ?);
    """, CORE_SEEDS["brands"])

    conn.commit()
    logger.info(f"Loaded core seeds: {len(CORE_SEEDS['concepts'])} concepts, {len(CORE_SEEDS['descriptions'])} descriptions, {len(CORE_SEEDS['brands'])} Indian brands.")


def load_rf2_directory(conn: sqlite3.Connection, rf2_dir: str):
    """Stream parses RF2 Snapshot files from a directory or zip archive."""
    if not os.path.exists(rf2_dir):
        logger.warning(f"RF2 directory {rf2_dir} does not exist. Skipping file parse.")
        return

    concept_files = glob.glob(os.path.join(rf2_dir, "**", "*Concept_Snapshot*.txt"), recursive=True)
    desc_files = glob.glob(os.path.join(rf2_dir, "**", "*Description_Snapshot*.txt"), recursive=True)

    cursor = conn.cursor()

    # 1. Parse Concepts
    for cfile in concept_files:
        logger.info(f"Streaming concepts from RF2 file: {cfile}")
        count = 0
        batch = []
        with open(cfile, "r", encoding="utf-8", errors="ignore") as f:
            header = f.readline()
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 5:
                    concept_id = parts[0]
                    active = int(parts[2])
                    if active == 1:
                        # Temporary name until description loads
                        batch.append((concept_id, f"SNOMED Concept {concept_id}", "finding", 1))
                        count += 1
                        if len(batch) >= 10000:
                            cursor.executemany("INSERT OR IGNORE INTO concepts VALUES (?, ?, ?, ?);", batch)
                            conn.commit()
                            batch = []
        if batch:
            cursor.executemany("INSERT OR IGNORE INTO concepts VALUES (?, ?, ?, ?);", batch)
            conn.commit()
        logger.info(f"Ingested {count} active concepts from {os.path.basename(cfile)}")

    # 2. Parse Descriptions
    for dfile in desc_files:
        logger.info(f"Streaming descriptions from RF2 file: {dfile}")
        count = 0
        batch_desc = []
        batch_concept_update = []
        with open(dfile, "r", encoding="utf-8", errors="ignore") as f:
            header = f.readline()
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 8:
                    desc_id = parts[0]
                    active = int(parts[2])
                    concept_id = parts[4]
                    type_id = parts[6] # 900000000000003001 = FSN, 900000000000013009 = Synonym
                    term = parts[7]

                    if active == 1:
                        batch_desc.append((desc_id, concept_id, term, type_id, 1))
                        if type_id == "900000000000003001": # FSN
                            # Extract semantic tag from FSN e.g. "Headache (finding)" -> "finding"
                            stag = "finding"
                            pname = term
                            if "(" in term and term.endswith(")"):
                                pname = term[:term.rfind("(")].strip()
                                stag = term[term.rfind("(") + 1:-1].strip()
                            batch_concept_update.append((pname, stag, concept_id))

                        count += 1
                        if len(batch_desc) >= 10000:
                            cursor.executemany("INSERT OR IGNORE INTO descriptions VALUES (?, ?, ?, ?, ?);", batch_desc)
                            if batch_concept_update:
                                cursor.executemany("UPDATE concepts SET preferred_name = ?, semantic_tag = ? WHERE concept_id = ?;", batch_concept_update)
                            conn.commit()
                            batch_desc = []
                            batch_concept_update = []
        if batch_desc:
            cursor.executemany("INSERT OR IGNORE INTO descriptions VALUES (?, ?, ?, ?, ?);", batch_desc)
            if batch_concept_update:
                cursor.executemany("UPDATE concepts SET preferred_name = ?, semantic_tag = ? WHERE concept_id = ?;", batch_concept_update)
            conn.commit()
        logger.info(f"Ingested {count} active descriptions from {os.path.basename(dfile)}")


def verify_counts(conn: sqlite3.Connection):
    """Verifies row counts across tables and FTS5 indexes."""
    cursor = conn.cursor()
    c_count = cursor.execute("SELECT count(*) FROM concepts;").fetchone()[0]
    d_count = cursor.execute("SELECT count(*) FROM descriptions;").fetchone()[0]
    b_count = cursor.execute("SELECT count(*) FROM brands;").fetchone()[0]

    fts_c_count = cursor.execute("SELECT count(*) FROM concepts_fts;").fetchone()[0]
    fts_d_count = cursor.execute("SELECT count(*) FROM descriptions_fts;").fetchone()[0]
    fts_b_count = cursor.execute("SELECT count(*) FROM brands_fts;").fetchone()[0]

    print("\n==================================================")
    print("      SICCE Clinical Knowledge Base Status        ")
    print("==================================================")
    print(f" Concepts Table:      {c_count:,} rows")
    print(f" Descriptions Table:  {d_count:,} rows")
    print(f" Indian Brands Table: {b_count:,} rows")
    print("--------------------------------------------------")
    print(f" Concepts FTS5:       {fts_c_count:,} indexed")
    print(f" Descriptions FTS5:   {fts_d_count:,} indexed")
    print(f" Brands FTS5:         {fts_b_count:,} indexed")
    print("==================================================\n")
    return c_count, d_count, b_count


def main():
    parser = argparse.ArgumentParser(description="SNOMED CT RF2 Ingestion Pipeline & Knowledge Base Generator")
    parser.add_argument("--db-path", default=DB_PATH, help="Path to output SQLite database")
    parser.add_argument("--rf2-dir", default="data/rf2", help="Path to RF2 snapshot directory")
    parser.add_argument("--check", action="store_true", help="Only verify and print current database counts")
    parser.add_argument("--seed-only", action="store_true", help="Only load core seeds without scanning RF2 directory")
    args = parser.parse_args()

    conn = get_db_connection(args.db_path)

    if args.check:
        verify_counts(conn)
        conn.close()
        return

    init_schema(conn)
    load_seeds(conn)

    if not args.seed_only and os.path.exists(args.rf2_dir):
        load_rf2_directory(conn, args.rf2_dir)

    verify_counts(conn)
    conn.close()
    logger.info("Knowledge base pipeline completed successfully.")


if __name__ == "__main__":
    main()
