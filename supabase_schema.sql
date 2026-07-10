-- Enable trigram extension for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Core SNOMED/LOINC/AYUSH Concepts table
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

-- Seed data
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('25064002', 'Headache (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'headache');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'head ache');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'sar dard');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'sar dard ho raha hai');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('25064002', 'sar dard tha');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('62315008', 'Diarrhoea (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'diarrhea');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'diarrhoea');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'loose motion');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'loose motions');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'pet kharab');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('62315008', 'pet kharab hai');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('60845006', 'Dyspnea on exertion (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('60845006', 'SOBOE');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('60845006', 'shortness of breath on exertion');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('60845006', 'dyspnea on exertion');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('60845006', 'breathlessness on walking');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('30711000', 'Edema of foot (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('30711000', 'pedal edema');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('30711000', 'pedal edema +');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('30711000', 'foot swelling');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('30711000', 'swelling in feet');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('21522001', 'Abdominal pain (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('21522001', 'abdominal pain');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('21522001', 'AP+');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('21522001', 'pain in abdomen');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('21522001', 'AP positive');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('21522001', 'stomach pain');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('367389006', 'Acid peptic disease (disorder)', 'disorder', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('367389006', 'APD');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('367389006', 'acid peptic disease');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('367389006', 'acidity');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('367389006', 'gastritis');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('422400008', 'Nausea (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('422400008', 'nausea');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('422400008', 'ulti jaisa lag raha hai');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('422400008', 'feeling like vomiting');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('422400008', 'nauseous');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('9651007', 'Heartburn (finding)', 'finding', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('9651007', 'heartburn');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('9651007', 'jalan in chest');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('9651007', 'chest burning');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('9651007', 'acidity in chest');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('37894001', 'Rheumatoid arthritis (disorder)', 'disorder', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('37894001', 'rheumatoid arthritis');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('37894001', 'RA');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('1221000189104', 'Amavata (finding)', 'finding', TRUE, '{"concept_id": "37894001", "relationship": "therapeutically_linked_to"}'::jsonb) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('1221000189104', 'amavata');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('1221000189104', 'joint stiffness with fever');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('1221000189104', 'ayurvedic arthritis');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('1221000189106', 'Vata vyadhi (finding)', 'finding', TRUE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('1221000189106', 'vata vyadhi');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('1221000189106', 'neuromuscular vata disorder');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('322262002', 'Paracetamol (substance)', 'substance', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('322262002', 'paracetamol');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('322262002', 'acetaminophen');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('322262002', 'PCM');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('322262002', 'Dolo 650');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('322262002', 'Dolo-650');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('322262002', 'Calpol');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('386864001', 'Pantoprazole (substance)', 'substance', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('386864001', 'pantoprazole');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('386864001', 'Pantocid 40');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('386864001', 'Pantocid');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('386864001', 'Pantosec');
INSERT INTO snomed_concepts (concept_id, preferred_name, semantic_tag, ayush_extension, cross_allopathy_mapping) VALUES ('387494008', 'Furosemide (substance)', 'substance', FALSE, NULL) ON CONFLICT (concept_id) DO UPDATE SET preferred_name = EXCLUDED.preferred_name, semantic_tag = EXCLUDED.semantic_tag, ayush_extension = EXCLUDED.ayush_extension, cross_allopathy_mapping = EXCLUDED.cross_allopathy_mapping;
INSERT INTO concept_synonyms (concept_id, term) VALUES ('387494008', 'furosemide');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('387494008', 'frusemide');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('387494008', 'Lasix 40mg');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('387494008', 'Lasix');
INSERT INTO concept_synonyms (concept_id, term) VALUES ('387494008', 'Lasix 40');