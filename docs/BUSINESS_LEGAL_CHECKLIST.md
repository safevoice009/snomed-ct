# BUSINESS & LEGAL FOUNDATION CHECKLIST — India Health-Tech Solo Founder

**Purpose:** Everything legally required to operate SICCE as a real business in India, sequenced so you spend almost nothing before you have revenue signals.
**Rule:** This is practical guidance, NOT legal advice. For incorporation filings and final contracts, use a reputable online platform (Vakilsearch/IndiaFilings/ClearTax tier) or a startup-focused CA/lawyer. Budget total: under ₹30k pre-revenue.

---

## STAGE 0 — Do These NOW (₹0, no entity needed)

| # | Action | Why | Notes |
|---|--------|-----|-------|
| 0.1 | **NRCeS SNOMED CT application (as an individual)** | Affiliate licenses are available to Indian professionals personally — incorporation does NOT block this | Already pending. Proceed |
| 0.2 | **ABDM Sandbox registration (individual/dev)** | Developer sandbox access works without a company | Already pending. Proceed |
| 0.3 | **Brand name final decision** | Everything below depends on it — see §BRAND | Do BEFORE trademark/incorporation |
| 0.4 | **Domain + social handles purchase** (~₹1–2k) | Cheap now, painful later if taken | .com/.in/.ai |

### BRAND WARNING — read honestly
The current project name **"SICCE" has problems**: (a) it reads/pronounces like "sick"/Italian profanity-adjacent in some markets, (b) **SICCE S.p.A.** is an existing Italian manufacturer with registered marks — trademark conflict risk in Class 9/11, (c) nobody buying enterprise healthcare infra says "let's buy Sicce".
**Action:** shortlist 5 alternative names. Check each against: MCA name search (mca.gov.in), IP India trademark search (ipindia.gov.in), domain availability, and a plain Google search. Pick once, then freeze.

---

## STAGE 1 — First Serious Pilot Signal → Incorporate (₹12–20k)

Trigger: a vendor/TPA asks "can you send us an agreement?" or gives written pilot interest. NOT before.

| # | Action | Details |
|---|--------|---------|
| 1.1 | **Private Limited Company** via SPICe+ (MCA portal) | B2B health-infra standard; buyers and DPIIT expect it. Requires **2 directors + 2 shareholders** — as solo founder, add a family member with nominal (e.g., 1%) shares and clear shareholder understanding in writing. Alternative: **OPC** (One Person Company, needs only nominee) — faster/solo, but some enterprises and investors treat it less seriously; convertible later at friction cost |
| 1.2 | Auto-issued with SPICe+: **PAN + TAN** | No extra step |
| 1.3 | **Company Current Account** | Choose a startup-friendly bank; keep books separate from day one |
| 1.4 | **GST registration** | B2B SaaS buyers claim input credit — they WILL ask for GST invoices. Register immediately rather than waiting for the ₹20L threshold |
| 1.5 | **DPIIT Startup India recognition** (free, online) | Benefits: income-tax holiday eligibility (80-IAC), self-certification under labour/environment laws, faster IPR fee rebates. Apply right after incorporation |
| 1.6 | Re-do registrations in company name | NRCeS org license, ABDM sandbox org profile, domain WHOIS |

---

## STAGE 2 — Trademark & IP (₹5–10k, after Stage 1)

| # | Action | Notes |
|---|--------|-------|
| 2.1 | **Trademark filing** for final brand: **Class 9** (software) + **Class 42** (SaaS/scientific services) | Govt fee ~₹4,500/class with Startup/dividual status; use a platform, not a big firm |
| 2.2 | **Logo/wordmark** consistent everywhere | Weak common-law rights otherwise |
| 2.3 | **IP hygiene:** all code authored via AI agents/contractors must be assigned to the company | Add assignment clauses to any contractor agreement; keep commits under company-owned accounts eventually |

---

## STAGE 3 — HEALTH-DATA REGULATION (the part that actually matters for this business)

### DPDP Act compliance — REAL DEADLINES (verified Aug 2026)
DPDP Rules 2025 were notified **13 Nov 2025**. Phased enforcement:
| Deadline | Obligation |
|----------|-----------|
| **13 Nov 2026** | Consent Manager framework operational |
| **~May 2027** | Full fiduciary obligations: granular consent, notice, breach reporting, rights workflows |

Your product processes health data = the most sensitive class. Required builds (map to existing repo):
- [x] Privacy policy (`static/privacy_policy.html`) — review against DPDP Rules notice format (items processed, purpose, retention period, grievance contact, rights)
- [x] Grievance officer page (`static/grievance_redressal.html`) — must be a NAMED HUMAN with working email; responses within prescribed timelines
- [x] Erasure workflow (`main.py` purge endpoint) — upgrade from in-memory purge to documented end-to-end erasure incl. backups; test with a real record
- [ ] Consent artifact records: consent logs retained **7 years**, linked to purpose + timestamp (engineering task when customers arrive)
- [ ] Breach playbook: notify Data Protection Board of India + affected users "without delay"; fines up to ₹200 Cr for failure — write the one-page playbook now, costs nothing
- [ ] Data-flow map: every processor touching PHI (Google Gemini API, Supabase, Render, GitHub) needs a **Data Processing Agreement** — list them in privacy policy
- Note: You are NOT a Significant Data Fiduciary at current scale (DPO/auditor/DPIA obligations kick in for large-volume handlers). Plan readiness, don't pay yet.

### SNOMED CT license terms — CRITICAL CAUTION for Phase 3 plan
Before open-sourcing the Hinglish→SNOMED lexicon (MASTER_DIRECTIVE Phase 3), **read the NRCeS/SNOMED International affiliate license redistribution clauses carefully.** SNOMED licensing historically restricts redistribution of coded content outside licensed jurisdictions/use. The safe pattern: open-source the Hinglish *phrases and mappings methodology*, require users to have their own affiliate license for the codes themselves. Get written clarity from NRCeS before publishing anything containing concept IDs.

### CDSCO / Software-as-Medical-Device risk
Under Medical Devices Rules 2017, software that informs diagnosis/treatment can qualify as a medical device. Your positioning protects you:
- Frame CDSS output as **coding-quality and documentation-safety alerts** for human review — never diagnosis/treatment recommendations
- Keep the clinical disclaimer prominent (exists: `static/terms_and_disclaimer.html`)
- Before any hospital pilot, take a one-hour opinion from a regulatory consultant (~₹10–15k) on whether current scope triggers registration

### ABDM operating policies
When selling to providers: comply with ABDM Health Data Management Policy, HIP/HIU participation terms, and NHCX participant agreements (each requires organizational identity → another reason Stage 1 comes before paid pilots).

---

## STAGE 4 — Contracts Needed at First Pilot (get templates from a platform lawyer, ₹10–25k total)

| Document | Purpose |
|----------|---------|
| Pilot Agreement / LOI template | Scope, success metrics, data handling, no-fee or discounted pilot terms |
| Master Service Agreement + SLA | Uptime %, support windows, liability cap (keep ≤ fees paid) |
| Data Processing Agreement | Mandatory under DPDP when customers push PHI through your API |
| Mutual NDA | For sales conversations |
| Clinical disclaimer & acceptable-use terms | "Output requires licensed clinician verification; not medical advice" |
| Website Terms of Use | Standard boilerplate |

---

## WHAT NOT TO DO (money burners)

1. ❌ Don't incorporate before a real buyer signal — entities create recurring compliance costs (annual ROC filings, auditor, ~₹15–30k/yr even at zero revenue)
2. ❌ Don't file trademark before the name search passes all four checks (MCA, IP India, domain, Google)
3. ❌ Don't hire a big law firm pre-revenue; platform lawyers + CA are enough until Series A or enterprise MSA negotiations
4. ❌ Don't publish the open-source lexicon before written NRCeS clarity on redistribution
5. ❌ Don't market CDSS as "clinical decision-making AI" — marketing language creates regulatory classification risk

## SEQUENCE SUMMARY

```
NOW (₹0):        NRCeS (individual) · ABDM sandbox · name decision · domain
PILOT SIGNAL:    Pvt Ltd + PAN/TAN + GST + bank · DPIIT recognition
NAME FROZEN:     Trademark Classes 9+42
BEFORE PILOTS:   DPDP gap-fix · breach playbook · DPAs with Gemini/Supabase/Render
                 · pilot agreement templates · CDSCO scoping opinion
AT SCALE:        Professional indemnity insurance · ISO 27001 · SDF-readiness review
```
