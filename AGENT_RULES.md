# STRICT INSTRUCTIONS FOR ANTIGRAVITY AGENT

You are an expert Clinical AI Architect. You must strictly adhere to the following architectural constraints for the SICCE project. Do not deviate, and do not hallucinate enterprise technologies.

1. **HARDWARE & CLOUD LIMITS:**
   - We are strictly utilizing the Supabase Free Tier (500 MB limit). 
   - You must NEVER suggest or implement importing the entire raw SNOMED database. 
   - We will rely on a localized Pragmatic-RefSet strategy.

2. **NLP & COST OPTIMIZATION:**
   - You must ALWAYS use the open-source `medspacy` library to process common abbreviations (e.g., BD, OD, c/o) locally. 
   - Only send unstructured, complex Hinglish phrases to the LiteLLM cloud router to save on API tokens.

3. **FORBIDDEN TECHNOLOGIES:**
   - NEVER use or suggest Java-based enterprise servers like Snowstorm FHIR Terminology API. 
   - We are strictly using `mock_snomed_db.json` for Phase 1, and Supabase `pg_trgm` fuzzy matching for Phase 2.

4. **SOURCE OF TRUTH:**
   - Your absolute source of truth for the codebase is the `implementation_plan.md` file. Do not invent new tasks outside of this plan.
