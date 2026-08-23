# Developer Sandbox Quickstart Guide (5-Minute Integration)

Welcome to the **SICCE API Sandbox**! Follow this quickstart to begin transforming unstructured Indian doctor prescriptions into ABDM FHIR R4 bundles, CDSS safety evaluations, and NHCX insurance claim payloads.

---

## 🔑 Authentication

Include your API key in the `X-API-KEY` request header for all requests:
```http
X-API-KEY: test-dev-key
```

*In Sandbox mode, use the default header `test-dev-key` to test endpoints immediately.*

---

## 🚀 Core API Endpoints

### 1. Parse Clinical Note & Generate FHIR R4
Converts messy doctor text, abbreviations, and Indian pharma brands into structured entities and an ABDM-compliant FHIR R4 Bundle.

**Endpoint**: `POST /api/v1/parse`

#### Python Example
```python
import httpx

url = "https://snomed-ct-parser-1.onrender.com/api/v1/parse"
headers = {"X-API-KEY": "test-dev-key", "Content-Type": "application/json"}
payload = {
    "text": "Pt c/o severe sar dard aur bukhar since 2 days. APD positive. Tab Pantocid 40mg OD, Tab Dolo 650mg BD."
}

res = httpx.post(url, headers=headers, json=payload)
data = res.json()

print("Parsed Symptoms:", data["extractions"]["symptoms"])
print("CDSS Alerts:", data.get("cdss_report", {}))
print("FHIR Bundle ID:", data.get("fhir_bundle", {}).get("id"))
```

#### Node.js / JavaScript Example
```javascript
const axios = require('axios');

async function parseClinicalNote() {
  const response = await axios.post('https://snomed-ct-parser-1.onrender.com/api/v1/parse', {
    text: "Sugar checkup: T2DM and high BP. Tab Glycomet 500 BD, Tab Telma 40 OD."
  }, {
    headers: { 'X-API-KEY': 'test-dev-key' }
  });

  console.log(response.data);
}

parseClinicalNote();
```

---

### 2. Clinical Decision Support (CDSS) Drug Interaction Check
Evaluates a list of medications and patient conditions for drug-drug interactions (DDIs), Penicillin allergies, and duplicate therapy.

**Endpoint**: `POST /api/v1/check-interactions`

#### cURL Example
```bash
curl -X POST "https://snomed-ct-parser-1.onrender.com/api/v1/check-interactions" \
     -H "X-API-KEY: test-dev-key" \
     -H "Content-Type: application/json" \
     -d '{
       "medications": ["Sildenafil 50mg", "Sorbitrate 10mg (Isosorbide Dinitrate)"],
       "allergies": ["Penicillin"],
       "patient_conditions": ["Angina Pectoris", "Erectile Dysfunction"]
     }'
```

---

### 3. NHCX Claim Pre-Adjudication
Evaluates FHIR claim bundles against IRDAI OPD sub-limits, provider registry checks, and medical necessity rules.

**Endpoint**: `POST /api/v1/pre-adjudicate`

#### cURL Example
```bash
curl -X POST "https://snomed-ct-parser-1.onrender.com/api/v1/pre-adjudicate" \
     -H "X-API-KEY: test-dev-key" \
     -H "Content-Type: application/json" \
     -d '{
       "bundle": {
         "resourceType": "Bundle",
         "entry": [
           {
             "resource": {
               "resourceType": "Claim",
               "id": "CLAIM-2026-001",
               "total": {"value": 1500, "currency": "INR"},
               "diagnosis": [{"diagnosisCodeableConcept": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10"}]}}],
               "item": [{"revenue": {"text": "Tab Telma 40mg OD"}}]
             }
           }
         ]
       }
     }'
```

---

## 📊 Status & Health Check
Verify API status and terminology database health anytime:
```bash
curl https://snomed-ct-parser-1.onrender.com/health
```
