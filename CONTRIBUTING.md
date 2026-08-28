# Contributing to SICCE

Thank you for your interest in contributing to the **SNOMED-India Clinical Coding Engine (SICCE)**!

As a health data interoperability and clinical coding platform, our priority is **clinical accuracy, zero code hallucination, and data privacy**.

---

## ⚖️ Clinical Coding Law #1: Zero Hallucination
When contributing to vocabulary mappings, NLP rules, or terminology resolvers:
- **Never synthesize or guess SNOMED CT / LOINC / RxNorm concept IDs.**
- All added codes must be verified against official SNOMED CT releases (or the official Snowstorm / C-DAC NRCeS browser).
- If a term or vernacular expression cannot be mapped to a standardized concept, return `coded: false` with the raw text preserved. Do not invent arbitrary identifiers.

---

## 🛠️ Development Workflow

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/<your-username>/snomed-ct.git
   cd snomed-ct
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run Test Suite**:
   Before submitting any Pull Request, ensure all tests pass:
   ```bash
   pytest tests/ -v
   ```

4. **Code Quality**:
   - Write clear, self-documenting code.
   - Include automated unit tests for any new clinical abbreviations, terminology mappings, or FHIR generators.
   - Maintain PEP 8 style guidelines.

---

## 🏥 Clinical & Architectural Questions
If you have suggestions for expanding regional drug formularies, AYUSH SNOMED extensions, or ABDM Milestone integrations, please open an Issue or start a Discussion on GitHub.
