# ABDM Sandbox Registration & Credentials Guide

**Purpose**: Guide for the founder to register and obtain ABDM Sandbox API credentials (`ABDM_CLIENT_ID` and `ABDM_CLIENT_SECRET`) from the National Health Authority (NHA).

---

## 📋 Overview

The **Ayushman Bharat Digital Mission (ABDM)** Sandbox is the official testing environment provided by the National Health Authority (NHA) for healthcare software developers in India.

- **Sandbox Portal URL**: [https://sandbox.abdm.gov.in/](https://sandbox.abdm.gov.in/)
- **Target Milestones**:
  - **M1**: ABHA Creation & Verification (Aadhaar OTP, Mobile OTP, Demographics)
  - **M2**: HIP (Health Information Provider) Record Push & Care Context Linking
  - **M3**: HIU (Health Information User) Consent Manager & Discovery

---

## 🚀 Step-by-Step Registration (Takes ~5 Minutes)

### Step 1: Create Sandbox Account
1. Open [https://sandbox.abdm.gov.in/](https://sandbox.abdm.gov.in/) in your browser.
2. Click on **"Register"** in the top right.
3. Select your entity type:
   - **Entity Type**: `Health Tech Startup / Software Developer` or `Individual Developer`
   - **Role**: `HIP & HIU` (Health Information Provider & Health Information User)
4. Fill in your Name, Official Email Address, and Mobile Number.
5. Verify your email and mobile with the OTPs received.

### Step 2: Register Your Application
1. Log in to the ABDM Sandbox Dashboard.
2. Navigate to **"My Applications"** -> **"Add New Application"**.
3. Enter application details:
   - **Application Name**: `SICCE Clinical Engine`
   - **Entity Name**: *Your Company / Organization Name*
   - **Use Case**: *Clinical NLP coding, Prescription OCR, SNOMED CT terminology resolution, and FHIR R4 care context generation for Indian outpatient clinics.*
   - **Callback URL**: `https://<your-domain>/api/v1/abdm/callback` (or your ngrok / local staging URL)
4. Click **Submit**.

### Step 3: Retrieve Sandbox API Credentials
1. Under your application in the dashboard, copy:
   - **Client ID** (`ABDM_CLIENT_ID`)
   - **Client Secret** (`ABDM_CLIENT_SECRET`)

---

## ⚙️ Configuring SICCE for Real Sandbox Mode

Once you have your credentials, configure your `.env` file or cloud environment variables:

```bash
# Set mode to sandbox (default is mock)
ABDM_MODE=sandbox

# Your ABDM Sandbox credentials from sandbox.abdm.gov.in
ABDM_CLIENT_ID="your_sandbox_client_id_here"
ABDM_CLIENT_SECRET="your_sandbox_client_secret_here"
```

When `ABDM_MODE=sandbox`, SICCE will automatically use `ABDMSandboxClient` in [`abha_gateway.py`](file:///c:/Users/unbou/snomedct/snomed%20ct/abha_gateway.py) to exchange client credentials for live ABDM access tokens.
