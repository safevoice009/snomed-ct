-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Core SNOMED/LOINC/AYUSH Concepts table
CREATE TABLE IF NOT EXISTS snomed_concepts (
    concept_id VARCHAR(50) PRIMARY KEY,
    preferred_name VARCHAR(255) NOT NULL,
    semantic_tag VARCHAR(50) NOT NULL,
    ayush_extension BOOLEAN DEFAULT FALSE,
    cross_allopathy_mapping JSONB DEFAULT NULL
);

-- Synonyms table for mapping terms to concept IDs
CREATE TABLE IF NOT EXISTS concept_synonyms (
    id SERIAL PRIMARY KEY,
    concept_id VARCHAR(50) REFERENCES snomed_concepts(concept_id) ON DELETE CASCADE,
    term VARCHAR(255) NOT NULL
);

-- Create GIN index for fast fuzzy searching via pg_trgm
CREATE INDEX IF NOT EXISTS idx_concept_synonyms_term_trgm ON concept_synonyms USING GIN (term gin_trgm_ops);

-- Database function for remote fuzzy matching RPC calls
CREATE OR REPLACE FUNCTION fuzzy_match_concept(search_term TEXT)
RETURNS TABLE (
    concept_id VARCHAR,
    preferred_name VARCHAR,
    semantic_tag VARCHAR,
    ayush_extension BOOLEAN,
    cross_allopathy_mapping JSONB,
    similarity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sc.concept_id, 
        sc.preferred_name, 
        sc.semantic_tag, 
        sc.ayush_extension, 
        sc.cross_allopathy_mapping,
        similarity(cs.term, search_term) AS similarity
    FROM concept_synonyms cs
    JOIN snomed_concepts sc ON cs.concept_id = sc.concept_id
    WHERE cs.term % search_term OR cs.term ILIKE '%' || search_term || '%'
    ORDER BY similarity(cs.term, search_term) DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 2. Better Auth & Clinical User Tables
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    image TEXT,
    role VARCHAR(50) DEFAULT 'doctor',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address VARCHAR(100),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
    account_id VARCHAR(255) NOT NULL,
    provider_id VARCHAR(50) NOT NULL,
    password TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. B2B Clinic API Keys & Audit Tracking
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
    key_value VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) DEFAULT 'Default EMR Key',
    requests_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clinical_audits (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    api_key_id VARCHAR(64) REFERENCES api_keys(id) ON DELETE SET NULL,
    note_snippet TEXT NOT NULL,
    symptoms_count INTEGER DEFAULT 0,
    diagnoses_count INTEGER DEFAULT 0,
    medications_count INTEGER DEFAULT 0,
    bundle_id VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed Concept Data
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('25064002', 'Headache (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'headache') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'head ache') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'sar dard') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'sar dard ho raha hai') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('62315008', 'Diarrhoea (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'diarrhea') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'diarrhoea') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'loose motion') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'loose motions') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'pet kharab') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('60845006', 'Dyspnea on exertion (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('60845006', 'SOBOE') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('60845006', 'dyspnea on exertion') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('30711000', 'Edema of foot (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('30711000', 'pedal edema') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('30711000', 'pedal edema +') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('21522001', 'Abdominal pain (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('21522001', 'abdominal pain') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('21522001', 'AP+') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('21522001', 'AP positive') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('367389006', 'Acid peptic disease (disorder)', 'disorder', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('367389006', 'APD') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('367389006', 'acid peptic disease') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('422400008', 'Nausea (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('422400008', 'nausea') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('422400008', 'ulti') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('422400008', 'ulti jaisa lag raha hai') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('1221000189104', 'Amavata (finding)', 'finding', TRUE, '{"concept_id": "37894001", "relationship": "therapeutically_linked_to"}'::jsonb) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('1221000189104', 'amavata') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('322262002', 'Paracetamol (substance)', 'substance', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('322262002', 'paracetamol') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('322262002', 'Dolo 650') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('386864001', 'Pantoprazole (substance)', 'substance', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('386864001', 'pantoprazole') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('386864001', 'Pantocid 40') ON CONFLICT DO NOTHING;

INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('387494008', 'Furosemide (substance)', 'substance', FALSE, NULL) ON CONFLICT (concept_id) DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('387494008', 'furosemide') ON CONFLICT DO NOTHING;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('387494008', 'Lasix 40mg') ON CONFLICT DO NOTHING;
