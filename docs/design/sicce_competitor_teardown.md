# SICCE Competitor Design Teardown — Indian Health-Tech Landing Pages
*Sources: live fetches of eka.care, veryfi.com (+/platform), practo.com, healthifyme.com, apollo247.com (Aug 2026). Hex values pulled from actual page markup/CSS.*

## Per-site teardown

### 1. Eka Care (eka.care) — AI-Native Health OS
- **Layout:** Hero = giant centered headline ("The AI-Native Ambient Healthcare Platform") → logo/product carousel ("Intelligent Documentation / Medical Records Analyser" rotating ticker) → "Product Suites: One Platform, Infinite Possibilities" 3-card grid (Scribe, EMR, Developer Portal, PHR) → feature sections each following CAPABILITIES label → H2 → 4 bullet columns → testimonials → footer. Classic B2B SaaS scroll narrative.
- **Colors:** Clinical white base with blue/violet gradient hero, soft pastel section tints. Safe, corporate, indistinguishable from any US health-SaaS.
- **Demo interactivity:** Near zero on the marketing page. A product-name ticker, hover states, video embeds. No working scribe demo, no sample input→output anywhere on the page despite selling an AI product.
- **Templated vs authored:** ~85% templated. "Save 12+ hours every week," "Digitise your practice in minutes," "Real Stories" testimonial block — every phrase is off the health-SaaS shelf. The only authored thing is the ABDM positioning itself.
- **Weaknesses:** (1) Sells AI but never shows it — no before/after of a real prescription becoming structured data. (2) Buzzword density ("Ambient Intelligence", "Multimodal AI Engine") with no proof pixels. (3) Four products dilute the story; nothing to *play with*. (4) Testimonials are name-drops without artifacts.

### 2. Veryfi (veryfi.com) — OCR API benchmark
- **Layout:** Hero "Documents into Data — securely, in seconds" → social proof strip (G2/Capterra 4.8, 1,000+ orgs) → SDK/API card grid → **interactive "Try It" tabbed demo** (Receipt / Invoice / W-2 / W-8BEN-E / W-9 / Check / Bank Statement) → live code snippet panel (Python client example) → industry verticals grid.
- **Colors:** Dark navy/indigo enterprise-dark theme, neon accent highlights, playful Hitchhiker's-Guide copy ("Don't Panic", "42", "Ship at Warp Speed") as the personality layer over serious compliance messaging (SOC2, HIPAA, GDPR badges).
- **Demo interactivity:** The best of the set — tabbed doc-type switcher feeding a live extraction preview, plus copy-paste code samples per language. This is why they're the benchmark.
- **Templated vs authored:** Layout templated; **voice authored**. The sci-fi humor copy and "no humans in the loop / own DGX H100s" security story are genuinely theirs.
- **Weaknesses:** (1) Demo is finance-doc-first; healthcare is buried in verticals. (2) Humor voice is polarizing and tonally whiplashy against HIPAA-seriousness. (3) Code panels are static screenshots-in-text, not editable/runnable. (4) Extraction preview shows clean printed docs — nobody's messy reality.

### 3. Practo (practo.com)
- **Layout:** Utility mega-header (Video Consultation / Find Doctors / Lab Tests / Surgeries tiles) → symptom-chip grid ("Period doubts or Pregnancy… CONSULT NOW") → doctor-search module → health articles → testimonials. Marketplace IA: everything is a funnel into booking.
- **Colors:** Signature Practo blue on white, high-volume card UI, red/orange CTA chips. Feels like a consumer app, not a clinic tool.
- **Demo interactivity:** Search autocomplete and city picker only. Everything else is navigation.
- **Templated vs authored:** Fully templated marketplace pattern — symptom chips, doctor cards, article SEO blocks could be any of 20 Indian health apps.
- **Weaknesses:** (1) Zero product demonstration; you must sign up to see anything. (2) Symptom chips feel dated and gimmicky. (3) Trust built via volume claims, never via showing competence. (4) Not relevant at all to a B2B/dev audience — wrong register for SICCE to imitate.

### 4. Healthify (healthifyme.com)
- **Layout:** Rebrand-forward hero ("Healthify and Berry Street Are Coming Together") → dual-CTA hero repeated twice (duplicated blocks visible even in DOM — sloppy) → "Try Ria, your personal AI coach" chat teaser → HealthifySnap photo-tracking explainer (3-step visual sequence) → LEARN/ACT/ASK triptych → app-download push.
- **Colors:** Deep teal-green (#21695C) on white — one of the few distinctive palettes in the set. Mobile-app aesthetic transplanted to web.
- **Demo interactivity:** Chat-teaser widgets and photo-upload teasers that route to app download — interactive-looking but dead-end on desktop.
- **Templated vs authored:** Mid. Ria/Snap are real product IP with real visuals; the LEARN/ACT/ASK framing is generic.
- **Weaknesses:** (1) Desktop site is an app-store billboard; duplicated hero blocks show template rot. (2) Every interaction ends in "Download the App". (3) AI coach teased but not demonstrable in-browser.

### 5. Apollo 24|7 (apollo247.com)
- **Layout:** Dense e-commerce portal: login bar, service mega-nav (Medicines/Doctors/Labs/Circle Membership/Insurance), long-form SEO text walls ("Apollo 24|7 - Your Most Trusted Healthcare Brand" + benefits lists), specialty pipe-lists for SEO.
- **Colors:** Apollo heritage palette confirmed in markup: deep green #125525 / mint #E9FAEE, gold #976707 / cream #FFF3D6, maroon #832541, orange #C2471A, yellow #FCB716 — trust-by-heritage, visually busy.
- **Demo interactivity:** None beyond commerce flows. Text-wall SEO pages dominate.
- **Templated vs authored:** Templated hospital-conglomerate web 2015 pattern; authority comes from the brand, not the design.
- **Weaknesses:** (1) SEO text walls actively ugly. (2) Six competing CTAs above the fold. (3) Legacy trust language ("40 years of legacy") instead of product proof.

## Teardown table

| Pattern | Who does it | Verdict |
|---|---|---|
| Centered hero + 3-card product grid + testimonials | Eka, Veryfi, all | **SLOP — avoid** |
| Compliance badge strips (HIPAA/SOC2/ISO/ABDM) | Eka, Veryfi, Apollo | Table-stakes; keep one line, don't build identity on it |
| "Save N hours weekly" time-saved claims | Eka ("12+ hrs"), Veryfi ("seconds") | **SLOP — avoid** unless shown live |
| Symptom/service chip grids | Practo, Apollo | **SLOP — avoid** (consumer-marketplace tell) |
| Logo walls + G2/Capterra stars | Veryfi, Eka | Fine but expected |
| Tabbed document-type demo (upload → structured JSON) | Veryfi only, finance docs | **The single highest-value pattern — steal the concept, own it for prescriptions** |
| Distinctive non-blue palette | Healthify (#21695C teal), Apollo (green/gold) | Blue-gradient SaaS = forgettable |
| Authored voice/personality in copy | Veryfi (Hitchhiker's) only | Huge gap in Indian health-tech |
| In-browser playable product demo | Nobody for clinical docs | **Gap** |
| Showing messy real-world input (scrawled Rx) | Nobody — everyone shows clean inputs | **Gap** |
| Hinglish/regional-language handling as a feature | Eka mentions "15+ languages" abstractly | **Gap** |
| FHIR/coded output visualization | Nobody markets it visually | **Gap** |
| Before→after transformation as the hero moment | Nobody leads with it | **Gap** |

## 5 Shock-Factor Moves SICCE Can Own

1. **"The Messy Rx Gauntlet" — live hero transformation.** A scrawled handwritten-style Hinglish prescription (SVG strokes, crossed-out meds, "1-0-1 khana ke baad") sits center-stage; user clicks **Decode** and watches ink annotations fly apart into a color-coded FHIR bundle tree (MedicationRequest, Dosage, SNOMED/LOINC codes highlighted). Veryfi demos clean receipts; nobody demos *chaos*. Single HTML: pre-authored SVG + CSS transitions + JS timeline. No upload needed for the demo — canned but visceral.

2. **Hinglish Confidence Meter — show the model thinking.** Split pane: left, prescription lines; right, each extracted field appears with a confidence dial and the *reasoning trail* in Hinglish↔English ("'suni' → suni? likely 'Sunil', context: patient name field"). Click any token to see alternatives. Nobody shows uncertainty honestly; it reads as radical transparency. Vanilla JS state machine over a hardcoded case file.

3. **FHIR Bundle X-Ray slider.** A rendered human-readable prescription on top; drag a slider right and it dissolves into raw JSON with syntax-highlighted resource links (arrows connecting `medication.reference` to the code). Like an anatomy view for data. Implementable with `input[type=range]` driving opacity/layout morph between two stacked layers.

4. **"Spot the Killer Interaction" game.** Gamified 30-second challenge: show two messy prescriptions; user picks which contains a dangerous drug interaction (e.g., warfarin + ibuprofen hidden in scrawl); SICCE's decoded overlay reveals the answer with a red flag animation, then a counter: "SICCE flags this in 0.4s. How long did you take?" Turns compliance-safety into play — no competitor has any interactive challenge at all.

5. **Prescription Autopsy Report (shareable artifact).** Paste-or-pick a sample Rx → instantly generates a beautiful one-page "autopsy": decoded meds table, detected abbreviations ("BD" → twice daily), flagged ambiguities, ABDM/FHIR readiness score ring, and a **Copy-as-JSON / Download-bundle** button that works client-side. The output is so pretty people screenshot it — the demo IS the marketing. Pure DOM rendering + Canvas/conic-gradient score ring; zero backend needed for the canned samples.

**Common thread:** every competitor either talks about AI or hides it behind signup. Five pages where the product transforms something *in front of you, in under a second, starting from genuine mess* would make SICCE look a category ahead — and each fits one self-contained HTML file.
