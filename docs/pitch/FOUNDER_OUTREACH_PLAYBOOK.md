# Founder B2B Outreach & Discovery Playbook

**Target Audience**: CTOs, Chief Product Officers, and Engineering Leads at Indian EMR/HIS Vendors (2–20 engineers) and Heads of Claims at Health Insurers / TPAs.

---

## 📩 LinkedIn Outreach Scripts

### Script 1: EMR / HIS Vendor CTOs (ABDM M1/M2 Compliance Angle)
> **Subject**: Quick question on ABDM M1/M2 FHIR compliance at [Company Name]
>
> Hi [First Name],
>
> Saw what you're building at [Company Name]. As a physician and clinical informatics engineer, I know how painful it is for EMR engineering teams to maintain full SNOMED CT terminology servers and map messy Indian doctor slang ("*Tab Pan-D*", "*APD+*", "*saas phoolna*") into NHA-compliant FHIR R4 bundles.
>
> We built **SICCE** — a lightweight, sub-50ms compliance engine in a box. It takes raw prescription text/photos and outputs validated ABDM FHIR R4 bundles with embedded drug-safety checks via a single REST API.
>
> We're running a 3-month sponsored pilot for select Indian EMR partners to handle their ABDM compliance pipeline. Would you be open to a 10-minute technical chat this week?
>
> Best,  
> [Founder Name]  
> Founder & Clinical Lead, SICCE  
> Sandbox: https://snomed-ct-parser-1.onrender.com

---

### Script 2: TPA / Insurance Claims Heads (NHCX & Pre-Adjudication Angle)
> **Subject**: Reducing claim rejection queries on NHCX OPD bundles
>
> Hi [First Name],
>
> With the rollout of NHCX and 100% cashless OPD mandates, TPAs are facing significant query overhead due to unmapped Indian pharma brands and ICD-10 medical necessity mismatches.
>
> We built a specialized pre-adjudication engine that validates incoming prescription bundles against IRDAI sub-limits and ICD-10 drug coherence in real-time, catching formatting and necessity errors *before* formal submission.
>
> Would you be open to seeing a 5-minute benchmark run on a sample batch of de-identified OPD claims?
>
> Best,  
> [Founder Name]

---

## 🛡️ Common Objections & Responses

| Objection | Founder Response |
| :--- | :--- |
| **"Why not just use free NRCeS / Snowstorm?"** | *"NRCeS provides the raw SNOMED terminology files, but not the clinical NLP layer that parses Indian brand names (like 'Pan-D' or 'Augmentin 625'), Hinglish abbreviations, dosage frequencies, or real-time CDSS interaction matrices. We provide the complete turnkey pipeline in a single sub-50ms call."* |
| **"How do you handle patient data privacy (DPDP Act)?"** | *"All clinical text is processed statelessly with automatic PHI de-identification before any semantic parsing. For enterprise partners with strict cloud data-residency policies, we also offer an air-gapped On-Premises Docker profile."* |
| **"Is your terminology real or mocked?"** | *"Our engine runs a full SQLite FTS5 index over official SNOMED CT release snapshots and a curated database of 500+ Indian pharmaceutical brands, with our benchmarked Medication F1 score exceeding 0.95."* |
