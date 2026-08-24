# DPDP BREACH RESPONSE PLAYBOOK — SICCE

**Version:** 1.0 · **Owner:** Founder (also default Grievance Officer until a DPO exists)
**Scope:** Any suspected or confirmed unauthorized access, disclosure, alteration, or loss of personal data (especially PHI) across API, database, LLM processors, or infrastructure.
**Legal basis:** Digital Personal Data Protection Act 2023 + DPDP Rules 2025 (notified 13 Nov 2025). Breach notification to the Data Protection Board of India (DPBI) and affected Data Principals must occur **without delay**. Failure-to-notify carries penalties up to ₹200 crore.

---

## PHASE 1 — DETECT & CONTAIN (Target: < 1 hour from alert)

1. Confirm whether a breach actually occurred (false positives are common: log anomalies ≠ exfiltration).
2. Contain first, investigate second:
   - Rotate all credentials/API keys possibly involved (Gemini, Supabase service keys, Render tokens, GitHub PATs).
   - Disable affected endpoints or take the deployment offline if exfiltration is ongoing.
   - Snapshot logs (`logs/`, Render logs, Supabase logs) BEFORE they rotate — preserve evidence with timestamps.
3. Record incident start time (first possible compromise) in the incident log.

## PHASE 2 — ASSESS (Target: within 24 hours)

Answer in writing (append to incident log):
- What data categories were exposed? (We process: clinical notes, extracted entities, FHIR bundles; PHI is sanitized before LLM routing — confirm sanitizer logs.)
- How many records / how many identifiable persons?
- Is the data encrypted at rest/in transit? Was it readable by the attacker?
- Root cause (known vs under investigation).

## PHASE 3 — NOTIFY (Statutory: without delay)

**A. Data Protection Board of India** — per Rules-prescribed format:
- Nature, scope, and timing of the breach
- Likely impact and mitigation steps taken
- Contact point for follow-up
Channel: DPBI portal/notification mechanism as specified when operational; email fallback to MeitY-nominated contact.

**B. Affected Data Principals** — plain-language notice containing:
- What happened, what data was involved
- Consequences likely for them
- Mitigations we have taken
- Contact for questions (Grievance Officer address from `/static/grievance_redressal.html`)
Delivery: email where held; site banner if contact data itself was breached.

**C. Customers (Data Processors/Fiduciaries under contract)** — notify per MSA/DPA terms (we will typically be processor for their patient data; their DPDP obligations may require faster internal SLAs — honor contract clocks).

## PHASE 4 — REMEDIATE (Target: < 72 hours)

1. Fix root cause; add regression test to CI proving the fix.
2. Force credential rotation sweep if cause was access-related.
3. Re-run full test suite + security tests before restoring service.
4. Document remediation in the incident log with evidence links.

## PHASE 5 — POST-INCIDENT REVIEW (within 7 days)

- Blameless written post-mortem committed to `docs/incidents/` (redacted).
- Update this playbook with lessons learned (version bump).
- Review whether the event changes our DPDP posture or requires customer notifications under any DPA.

---

## INCIDENT LOG TEMPLATE

```
INCIDENT-ID: INC-YYYYMMDD-NN
DETECTED AT (UTC):
CONTAINED AT (UTC):
DATA CATEGORIES AFFECTED:
RECORD COUNT (est.):
ROOT CAUSE:
NOTIFICATIONS: DPBI sent [date/time] · Principals sent [date/time] · Customers [date/time]
REMEDIATION COMMIT(S):
POST-MORTEM LINK:
```

## CONTACTS (fill in at incorporation)

| Role | Name | Contact |
|---|---|---|
| Incident Lead / Founder | ______ | ______ |
| Grievance Officer | ______ | (must match public page) |
| Hosting escalation (Render) | — | support ticket / status page |
| DB escalation (Supabase) | — | support portal |
| Legal counsel | ______ | engage platform lawyer at pilot stage |
