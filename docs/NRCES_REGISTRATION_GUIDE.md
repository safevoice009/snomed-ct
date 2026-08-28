# Step-by-Step NRCeS SNOMED CT License Application Guide

Follow these simple steps to obtain your official **SNOMED CT India Edition Release**. The license is **100% free** for Indian developers, healthcare professionals, and healthcare organizations under the National Release Centre for EHR Standards (NRCeS), Ministry of Health & Family Welfare (MoHFW).

---

## ⏱️ Total Time: ~3 to 5 minutes

### Step 1: Open the NRCeS Portal
- Go to: **[https://www.nrces.in/](https://www.nrces.in/)**
- Click on **"Register for SNOMED CT Affiliate License"** (or go directly to [https://www.nrces.in/affiliate-license](https://www.nrces.in/affiliate-license)).

---

### Step 2: Fill Out Account Details
- **User Category**: Select **"Individual"** (or **"Commercial Organization"** if you have a registered company).
- **Full Name**: Your legal name.
- **Email Address**: Your primary email address (verification link will be sent here).
- **Mobile Number**: Your 10-digit Indian phone number.
- **Country**: India.

---

### Step 3: Pre-Filled Answers for Intended Use (Copy & Paste These)

When the form asks for your project description and intended use of SNOMED CT, paste these exact responses:

#### 1. Purpose of Using SNOMED CT:
> *"Development of an ABDM-compliant clinical terminology translation middleware (SICCE) for Indian healthcare providers and EMR systems. The system maps outpatient clinical notes, diagnostic findings, and Indian pharmaceutical products to standard SNOMED CT concepts to support Ayushman Bharat Digital Mission (ABDM) Milestone 1 & 2 FHIR R4 OP Consultation records."*

#### 2. Scope of Implementation:
> *"Internal development, terminology search indexing (SQLite FTS5), and ABDM FHIR bundle generation for Indian outpatient clinics and EMR partners."*

#### 3. Primary Target Territory:
> *"India (National Release Territory)"*

---

### Step 4: Accept Terms & Submit
1. Accept the standard SNOMED International Affiliate License agreement.
2. Click **Submit Application**.
3. Check your email for the verification link and confirm your account.

---

### Step 5: Download the RF2 Snapshot Package
Once approved (typically within 1–2 business days):
1. Log in to the [NRCeS Member Portal](https://www.nrces.in).
2. Go to **Downloads** $\rightarrow$ **SNOMED CT India Edition Releases**.
3. Download the latest Snapshot ZIP (e.g. `SnomedCT_InternationalRF2_PRODUCTION_*.zip` + India Extension).
4. Extract the `.txt` files from the `Snapshot/Terminology/` folder into your repository at:
   ```
   data/rf2/
   ```
   *(Files: `sct2_Concept_Snapshot_*.txt` and `sct2_Description_Snapshot-en_*.txt`)*
5. Run the one-command loader:
   ```powershell
   python scripts/load_rf2.py
   ```
   *The database will immediately ingest 350,000+ concepts, and `/health` will turn 100% green!*
