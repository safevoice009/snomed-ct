# OpenSpec Tasks: Enterprise Health Moats Suite

- [x] 1. Build NHCX Claim Pre-Adjudication Engine (`nhcx_adjudicator.py`) <!-- id: 1 -->
  - [x] 1.1 Implement IRDAI/TPA rule engine (code coherence, necessity checks, duration validation) <!-- id: 1.1 -->
  - [x] 1.2 Implement pre-submission scoring algorithm (0-100% approval probability) <!-- id: 1.2 -->
  - [x] 1.3 Add `/api/v1/nhcx/pre-adjudicate` endpoint in `main.py` <!-- id: 1.3 -->
  - [x] 1.4 Add NHCX Pre-Adjudication UI tab in `static/index.html` and `static/app.js` <!-- id: 1.4 -->

- [x] 2. Build ABDM M1/M2 ABHA Gateway (`abha_gateway.py`) <!-- id: 2 -->
  - [x] 2.1 Implement ABHA ID generation and OTP verification simulation/bridge <!-- id: 2.1 -->
  - [x] 2.2 Implement Care Context linkage and M2 consultation record dispatch <!-- id: 2.2 -->
  - [x] 2.3 Add `/api/v1/abdm/*` endpoints in `main.py` <!-- id: 2.3 -->
  - [x] 2.4 Add ABHA Card creation modal in `static/index.html` and `static/app.js` <!-- id: 2.4 -->

- [x] 3. Build WhatsApp & Telephony Doctor Ingestion Bot (`webhook_handler.py`) <!-- id: 3 -->
  - [x] 3.1 Implement WhatsApp webhook handler for incoming audio/image messages <!-- id: 3.1 -->
  - [x] 3.2 Ingest prescription photos and auto-format ABDM consultation response <!-- id: 3.2 -->
  - [x] 3.3 Add `/api/v1/webhook/whatsapp` endpoint in `main.py` <!-- id: 3.3 -->

- [x] 4. Build Air-Gapped DPDP Enterprise Appliance Config <!-- id: 4 -->
  - [x] 4.1 Create `Dockerfile.onprem` and `docker-compose.enterprise.yml` for offline LAN deployment <!-- id: 4.1 -->
  - [x] 4.2 Validate end-to-end integration and run production test suite <!-- id: 4.2 -->
  - [x] 4.3 Commit, push to GitHub remotes, and deploy to live Render production <!-- id: 4.3 -->
