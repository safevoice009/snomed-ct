# SICCE Production Deployment Checklist & Runbook

**Target SLA**: Deploy from clean checkout to live production in < 10 minutes.

---

## 🔑 1. Required Environment Variables

Configure these environment variables in your hosting dashboard (Render / Docker / On-Prem):

| Variable Name | Required | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `ALLOWED_ORIGINS` | **Yes** | `https://snomed-ct-parser-1.onrender.com,http://localhost:8000` | Comma-separated CORS origin whitelist. |
| `ABDM_MODE` | **Yes** | `mock` | `mock` (developer preview), `sandbox` (official NHA dev), or `production`. |
| `API_KEYS` | **Yes** | - | Comma-separated valid API keys for client access (e.g. `sicce_live_sec_xxx`). |
| `WHATSAPP_WEBHOOK_SECRET` | Optional | - | Secret string for authenticating inbound webhook traffic. |
| `GEMINI_API_KEY` | Optional | - | LLM fallback key for complex clinical narrative parsing. |
| `SUPABASE_URL` | Optional | - | Cloud PostgreSQL URL for distributed fuzzy matching. |
| `SUPABASE_KEY` | Optional | - | Service role / anon key for Supabase cloud instance. |
| `MIN_TERMINOLOGY_CONCEPTS` | Optional | `100000` | Minimum concepts required for `/health` to report `healthy`. |
| `PORT` | Auto | `10000` | Injected automatically by Render / Cloud hosting. |

---

## 🐳 2. Local Docker Verification & Runbook

To build and run locally with Docker Desktop:

```powershell
# 1. Start Docker Desktop, then build the image
docker build -t sicce:latest .

# 2. Run the container on port 8000
docker run -d -p 8000:10000 --name sicce-container -e ALLOWED_ORIGINS="*" -e API_KEYS="test-dev-key" sicce:latest

# 3. Verify Health & Telemetry
curl http://localhost:8000/health

# 4. Run test clinical note parse
curl -X POST http://localhost:8000/api/v1/parse `
  -H "Content-Type: application/json" `
  -H "X-API-KEY: test-dev-key" `
  -d '{"text": "Patient c/o loose motions and sar dard. APD positive. Tab Pantocid 40mg OD, Tab Dolo 650mg BD."}'
```

---

## ☁️ 3. Deploying to Render.com

SICCE includes a native [`render.yaml`](../render.yaml) blueprint:

1. **Connect GitHub Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com/) -> **New** -> **Blueprint**.
   - Connect `https://github.com/safevoice009/snomed-ct.git`.
2. **Review Service Blueprint**:
   - **Service Name**: `snomed-ct-parser`
   - **Environment**: `Docker` (using root `Dockerfile`)
   - **Health Check Path**: `/health`
3. **Set Environment Variables**:
   - Add your `ALLOWED_ORIGINS`, `API_KEYS`, and `GEMINI_API_KEY`.
4. **Click Deploy**:
   - Render will build the container and deploy the web service in ~2 minutes.

---

## ✅ 4. Post-Deployment Smoke Test (1-Minute Verification)

Run these 3 commands against your live production domain:

```powershell
$DOMAIN = "https://snomed-ct-parser-1.onrender.com"
$API_KEY = "your_configured_api_key"

# 1. Health Status (Verify non-crash & unseeded status warning)
curl "$DOMAIN/health"

# 2. Clinical Parsing & FHIR R4 Bundle Output
curl -X POST "$DOMAIN/api/v1/parse" `
  -H "Content-Type: application/json" `
  -H "X-API-KEY: $API_KEY" `
  -d '{"text": "Sugar checkup: T2DM and high BP. Tab Glycomet 500 BD, Tab Telma 40 OD."}'

# 3. Cost & Latency Summary
curl "$DOMAIN/api/v1/metrics/summary" -H "X-API-KEY: $API_KEY"
```
