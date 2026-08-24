# DESIGN & FUNCTIONALITY INSPIRATION DOSSIER

**Purpose:** Research-verified patterns from the best sites in our four adjacent categories, mapped to concrete upgrades for SICCE. Clone the pattern, improve the execution.
**Method:** Live site analysis + DX best-practice research, Aug 2026.

---

## CATEGORY 1 — Document OCR APIs (our closest analogs)

### Veryfi (veryfi.com) — the benchmark
| Pattern | What they do | Steal for SICCE |
|---|---|---|
| Dual-CTA hero | "Start Free Trial" + **"See It Work First"** → dedicated /demo page | We already have workbench-first hero ✓. Add a secondary "Watch 60s walkthrough" path later |
| **Tabbed live demo widget** | "Try It" tabs by doc type: Receipt / Invoice / Check / Bank Statement | Our workbench has OCR/Text modes. ADD sample-type tabs: OPD Slip / Discharge Summary / Lab Report / AYUSH Rx — each preloading a different sample (we have 3 chips; extend to 5-6 with distinct outputs) |
| Code-next-to-output | API snippet paired with the parsed result visual | Our Dev Hub shows code only. ADD a split view: code left, live JSON response right (we can wire the real /api/v1/parse response into it) |
| "Ship at Warp Speed" | SDK section with fake terminal showing webhooks firing | Add a terminal-style block showing our webhook/metrics events (real formats) |
| Logo marquee w/ captions | "Navan Expense is powered by Veryfi OCR" | WE CANNOT (no customers yet — honesty law). Alternative we already use: built-in-public. Revisit post-pilots |
| Interactive API explorer | docs.veryfi.com/interactive-api — try requests in docs | P1: our /docs (Swagger) already has Try-it-out. Link it prominently from the Dev Hub card |

### Nanonets (nanonets.com/ocr-api)
| Pattern | What they do | Steal for SICCE |
|---|---|---|
| **"Get your free API key" block** | Shows a sample key visual + 1-click path to keys | P0: Add a "Get your sandbox key" card in Dev Hub → links to sign-up/API-keys endpoint. Reduces TTFC (time-to-first-call) |
| Per-doc-type SEO pages | 300+ extractor landing pages (invoice-ocr, passport-ocr…) | P2 (post-RF2): /prescription-ocr, /discharge-summary-fhir, /nhcx-claim-coding pages — each = organic search magnet |
| Stats band | ">1B documents · 90% time savings · 10x productivity" | We have the honest stats band ✓ (40 tests, FHIR R4, 15+ rules, 99+ brands). Keep honest numbers only |
| Multi-language code tabs | Python/Java/cURL/Node samples | We have 3 tabs ✓. Add request AND response side-by-side |
| Live demo upload | "Upload your own documents, test pre-trained models" | Our workbench ✓ — but ADD drag-and-drop anywhere on the page + paste-image support |

---

## CATEGORY 2 — Medical Scribes (design language references)

### Heidi Health / Commure Scribe / Freed
| Pattern | What they do | Steal for SICCE |
|---|---|---|
| **Triple proof-point hero** | Commure: "**99.4%** accuracy · **43-second** charts · **$59**/month" | Our hero proofrow exists ✓. Upgrade to 3 big numbers with count-up: **40** tests · **R4** FHIR · **0** stored PHI |
| Free trial, no card | "Free trial with no credit card" (Heidi) | Our sandbox needs no signup ✓ — SAY IT LOUDER: badge on workbench "No signup · 1,000 free calls" |
| Specialty pages | "From cardiology to paediatrics…" | P2: per-specialty sample presets (Peds Rx, derm, ortho) in the workbench chips |
| Quantified outcomes | "Finish charting in 2 minutes, not 20" (Scribeberry) | When eval data exists: "Parse an OPD note in X seconds" — measured, not claimed |

---

## CATEGORY 3 — Developer API Experience (the biggest functionality wins)

### Deepgram / Stripe / Twilio patterns
| Pattern | What they do | Steal for SICCE |
|---|---|---|
| **No-signup API playground** | Deepgram: "Make a request without writing any code! No sign-up required!" | P0: Our workbench IS this — but add a **"Copy as cURL"** button that exports the exact last request as a runnable curl with the sandbox key |
| **TTFC metric** | Time To First Call = the DX north-star | Design goal: landing → first successful parse in <60s. Current flow is close; remove the Key dropdown friction (auto-select sandbox key) |
| Fast-proof vs deep-eval paths | Preloaded request + visible response for tourists; editable params + code export for serious buyers | Workbench = fast path ✓. ADD "export request as cURL/Python" = deep path |
| Operator-voice copy | "Run a sample customer lookup" not "Execute query" | Rename button: "Parse & Extract Entities" ✓ good. Tab labels could read "Parse an OPD slip" style — P2 polish |
| **Status page as trust** | Veryfi runs a public status page | We have /health ✓. P2: pretty status page at /status rendering the same JSON with uptime history |
| Instrument the playground | Track request-starts, successes, copies, conversion | We have /api/v1/metrics/summary ✓. Add copy-button + parse-success event counters to it |

### DX research consensus (Postman/Beefed/Raze 2025-26)
- Docs quality = top adoption decision factor; runnable examples > prose
- Every code sample must be copy-paste runnable with expected request + expected response + one common error with remedy
- Show "How do I authenticate?" → "How do I make a working request?" → "How do I handle errors?" in that order
- Sandbox with ephemeral keys + visible request logs converts trials

---

## CATEGORY 4 — India Health-Tech (Eka Care)
- Clean clinical light theme ✓ (we match now)
- ABDM badges displayed prominently — we show honestly-labeled progress instead until certified
- Free tier as acquisition (5 consults/day) — our 1,000 free inferences matches ✓

---

## PRIORITIZED BUILD LIST FOR SICCE

### P0 — Do next (high impact, low effort)
1. **"Copy as cURL" button** on workbench → exports last parse request with sandbox key (Deepgram pattern)
2. **"Get your free sandbox key" card** in Dev Hub with sample-key visual (Nanonets pattern)
3. **Request/Response split view** in Dev Hub: wire real parse output next to the code snippet (Veryfi/Resend pattern)
4. Remove key-selection friction: auto-use sandbox key, hide dropdown unless multiple keys

### P1 — After RF2 lands
5. Sample-type tabs: OPD Slip / Discharge Summary / Lab Report / AYUSH (Veryfi doc-type tabs)
6. Drag-and-drop + paste-image upload anywhere on workbench
7. /status pretty page rendering /health + metrics history
8. Link Swagger Try-it-out prominently from Dev Hub

### P2 — Post-pilots (needs data/customers)
9. Per-use-case SEO pages: /prescription-ocr, /nhcx-claim-coding, /discharge-summary-fhir
10. Specialty preset chips (peds/derm/ortho samples)
11. Logo wall + case studies — ONLY with real customer permission
12. "Parse in X seconds" measured claim once eval data exists

---

## ANTI-PATTERNS TO AVOID (learned from research)
- ❌ Logo walls with pilots presented as deployments (Scribeberry calls this out explicitly — buyers check)
- ❌ Accuracy % without published methodology
- ❌ Opaque pricing (Augnito criticized everywhere for it) — our published rates are a differentiator
- ❌ Treating the playground as a dev toy instead of a conversion surface — instrument it
