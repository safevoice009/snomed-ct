-- scripts/export_supabase_refset.sql
-- Curated Indian OPD Reference Set (Task 1.5A) for Supabase PostgreSQL / Cloud Terminology

CREATE TABLE IF NOT EXISTS snomed_concepts (
    concept_id VARCHAR(32) PRIMARY KEY,
    preferred_name TEXT NOT NULL,
    semantic_tag VARCHAR(32) NOT NULL DEFAULT 'finding',
    icd10_code VARCHAR(16),
    active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS snomed_descriptions (
    id SERIAL PRIMARY KEY,
    concept_id VARCHAR(32) REFERENCES snomed_concepts(concept_id),
    term TEXT NOT NULL,
    term_type VARCHAR(16) NOT NULL DEFAULT 'synonym',
    language_code VARCHAR(8) NOT NULL DEFAULT 'en-IN'
);

CREATE TABLE IF NOT EXISTS indian_pharma_brands (
    id SERIAL PRIMARY KEY,
    brand_name TEXT NOT NULL,
    generic_name TEXT NOT NULL,
    category TEXT,
    snomed_id VARCHAR(32) REFERENCES snomed_concepts(concept_id),
    typical_doses TEXT,
    synonyms TEXT
);

-- Seed Core OPD Reference Set
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, icd10_code, active) VALUES
('38341003', 'Essential hypertension', 'disorder', 'I10', true),
('44054006', 'Type 2 diabetes mellitus', 'disorder', 'E11', true),
('367389006', 'Acid peptic disease', 'disorder', 'K27', true),
('95892003', 'Acute gastroenteritis', 'disorder', 'A09', true),
('10509002', 'Acute bronchitis', 'disorder', 'J20', true),
('61582004', 'Allergic rhinitis', 'disorder', 'J30.9', true),
('195967001', 'Asthma', 'disorder', 'J45', true),
('13645005', 'Chronic obstructive pulmonary disease', 'disorder', 'J44.9', true),
('370992007', 'Dyslipidemia', 'disorder', 'E78.5', true),
('40930008', 'Hypothyroidism', 'disorder', 'E03.9', true),
('90560007', 'Hyperuricemia and Gout', 'disorder', 'M10.9', true),
('69896004', 'Rheumatoid arthritis', 'disorder', 'M06.9', true),
('239872002', 'Osteoarthritis of knee', 'disorder', 'M17.9', true),
('68566005', 'Urinary tract infection', 'disorder', 'N39.0', true),
('266569009', 'Benign prostatic hyperplasia', 'disorder', 'N40', true),
('235856003', 'Fatty liver disease', 'disorder', 'K76.0', true),
('10743008', 'Irritable bowel syndrome', 'disorder', 'K58.9', true),
('37796009', 'Migraine', 'disorder', 'G43.9', true),
('398057008', 'Tension-type headache', 'disorder', 'G44.2', true),
('21897009', 'Generalised anxiety disorder', 'disorder', 'F41.1', true),
('370143000', 'Major depressive disorder', 'disorder', 'F32.9', true),
('193462001', 'Primary insomnia', 'disorder', 'G47.0', true),
('87522002', 'Iron deficiency anemia', 'disorder', 'D50.9', true),
('34713006', 'Vitamin D deficiency', 'disorder', 'E55.9', true),
('190634004', 'Vitamin B12 deficiency', 'disorder', 'E53.8', true),
('19839007', 'Tinea corporis', 'disorder', 'B35.4', true),
('301011002', 'Scabies', 'disorder', 'B86', true),
('11381005', 'Acne vulgaris', 'disorder', 'L70.0', true),
('24079001', 'Atopic dermatitis', 'disorder', 'L20.9', true),
('266599000', 'Dysmenorrhea', 'disorder', 'N94.6', true),
('237055002', 'Polycystic ovarian syndrome', 'disorder', 'E28.2', true),
('202794002', 'Cervical spondylosis', 'disorder', 'M47.812', true),
('202796000', 'Lumbar spondylosis with Sciatica', 'disorder', 'M47.816', true),
('38362002', 'Dengue fever', 'disorder', 'A90', true),
('4834000', 'Enteric fever (Typhoid)', 'disorder', 'A01.0', true),
('363746003', 'Acute pharyngitis / Tonsillitis', 'disorder', 'J02.9', true),
('9826008', 'Conjunctivitis', 'disorder', 'H10.9', true),
('25064002', 'Headache', 'finding', 'R51', true),
('386661006', 'Fever', 'finding', 'R50.9', true),
('49727002', 'Cough', 'finding', 'R05', true),
('267036007', 'Dyspnea on exertion', 'finding', 'R06.0', true),
('422587007', 'Nausea', 'finding', 'R11.0', true),
('422400008', 'Vomiting', 'finding', 'R11.1', true),
('62315008', 'Diarrhoea', 'finding', 'A09', true),
('21522000', 'Abdominal pain', 'finding', 'R10.9', true),
('267038008', 'Edema of foot', 'finding', 'R60.0', true),
('57676002', 'Joint pain', 'finding', 'M25.50', true),
('29857009', 'Chest tightness', 'finding', 'R07.89', true),
('16331000', 'Heartburn', 'finding', 'R12', true),
('91175000', 'Sneezing', 'finding', 'R06.7', true),
('64531003', 'Rhinorrhea', 'finding', 'J34.89', true),
('56018004', 'Wheezing', 'finding', 'R06.2', true),
('80313002', 'Palpitations', 'finding', 'R00.2', true),
('14760008', 'Constipation', 'finding', 'K59.00', true),
('13791008', 'Generalized weakness', 'finding', 'R53.1', true),
('79890006', 'Loss of appetite', 'finding', 'R63.0', true)
ON CONFLICT (concept_id) DO UPDATE 
SET preferred_name = EXCLUDED.preferred_name,
    semantic_tag = EXCLUDED.semantic_tag,
    icd10_code = EXCLUDED.icd10_code;
