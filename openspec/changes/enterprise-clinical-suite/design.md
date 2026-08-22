# Design Document: Enterprise Clinical Suite Expansion

## 1. Interactive ROI & Cost Calculator
- **Component**: `.roi-calculator-card` inside a new `#roi-calculator` section.
- **Formulas**:
  - `Veryfi Cost (USD -> INR)`: $\text{Volume} \times \$0.08 \times 87.5 = \text{Volume} \times ₹7.00$
  - `SICCE Cost (INR)`: $\text{Volume} \times ₹0.18$
  - `Annual Savings`: $(\text{Veryfi Cost} - \text{SICCE Cost}) \times 12$
  - `Savings %`: $97.4\%$

## 2. Real-Time Drag-and-Drop / File Upload
- **Component**: `#optical-upload-dropzone` with `FileReader` API for instant client-side rendering on canvas.
- **Workflow**: Reads user-uploaded JPEG/PNG, displays in optical stage, runs optical OCR text extraction mock or endpoint, and renders live bounding boxes with interactive hover cross-inspection.

## 3. Clinical Drug-Drug Interaction (DDI) & Safety Alert Engine
- **Module**: `ddi_engine.py` / backend logic & frontend warning alert banners.
- **Rules**:
  - `Pantoprazole / Antacid + Norfloxacin`: Chelation alert (administer 2 hours apart).
  - `Paracetamol / Dolo > 4000mg/day`: Hepatotoxicity maximum daily dose warning.
  - `Lasix (Furosemide) + NSAIDs`: Renal perfusion and diuretic blunting warning.

## 4. Vernacular Patient Dosage Generator
- **Dictionary**: Multi-lingual schedule mapping for standard frequencies (`OD`, `BD`, `TDS`, `QID`, `HS`, `SOS`, `pc`, `ac`) across Hindi, Marathi, Tamil, Telugu, and Bengali.
- **Output Tab**: "Patient Vernacular Card" in right inspector pane.

## 5. Developer Postman & OpenAPI Downloader
- **Endpoint**: `/api/v1/postman-collection` returning valid Postman v2.1 collection JSON and `/openapi.json` download.
