# SICCE Aesthetic Council — Design DNA Research & Creative Direction
Research date: 2026-08-26

---

## PART 1 — DESIGN DNA BREAKDOWN

### 1. NOUS RESEARCH (nousresearch.com)
**Identity thesis:** underground technical-art imprint × machine oracle. The site behaves like a model generating itself.

- **Typography:** Clean geometric sans for prose; heavy condensed UPPERCASE for mastheads/stamps. Monospace metadata is a *design element*: every content block carries provenance markers like `OUTPUT 96 / SEED: 3573860127`. Version numbers and release codenames appear prominently as graphics.
- **Color philosophy:** Dark by default; strict 2–4 ink duotone discipline (pale cyan, cobalt/navy, black, cream/tan, acid yellow). Atmosphere mandatory — mist/particles/glow; flat designs are considered off-brand.
- **Motion language:** Terminal-first. ASCII banners, TUI chrome, personality-bearing spinners. The web presence borrows console cadence, not consumer-app polish.
- **Voice:** Manifesto, not features. "Artificial intelligence made human." "Advance human rights and freedoms by creating and proliferating open source language models." Ideological conviction stated plainly.
- **Insider credibility:** Provenance theater (seeds, output counts), first-class community-infrastructure links (HuggingFace, GitHub, Discord before any sales CTA), and zine/xerox print culture — looking like a self-published artifact signals you're of the scene, not selling to it.

### 2. LINEAR (linear.app)
**Identity thesis:** darkness as native medium; precision-engineered luminance.

- **Typography:** Inter Variable with OpenType `cv01` + `ss03` globally — alternates make stock Inter into *their* typeface. Signature weight **510** (between regular and medium). Aggressive negative tracking at display sizes (−1.584px @ 72px). Berkeley Mono for anything technical. Max weight 590 — never bold.
- **Color philosophy:** Almost fully achromatic. Canvas `#08090a`, luminance-stepped surfaces (`rgba(255,255,255,0.02→0.05)`), whisper-thin semi-transparent white borders. ONE chromatic accent — indigo `#5e6ad2` / `#7170ff` — reserved strictly for interaction/CTA. Color is never decoration.
- **Motion language:** Restraint as flex. Product truth rendered live on the marketing page — real issues, real Slack threads, real diffs animating as if the app were running. Elevation via background luminance steps, never drop shadows.
- **Voice:** Declarative aphorisms. "A new species of product tool." "Built for the future. Available today." Zero self-praise; customers supplied the superlatives ("Linear is excellent, just excellent" — Opendoor CEO).
- **Insider credibility:** Engineering-drawing captions (`FIG 0.2`, `FIG 0.3`), real named engineers from OpenAI/Ramp as testimonials, changelog-as-culture, density of authentic product UI on every screen.

### 3. VERCEL (vercel.com)
**Identity thesis:** minimalism as compiler principle; text minified for production.

- **Typography:** Geist Sans weight 600 with the most extreme negative tracking in the industry (−2.4 to −2.88px @ 48px) — headlines feel minified. Geist Mono UPPERCASE labels connect marketing to the developer console. Ligatures on globally. Three weights only: 400 read / 500 interact / 600 announce.
- **Color philosophy:** Gallery emptiness — `#ffffff` on `#171717`, nothing else. Workflow accents (Develop Blue `#0a72ef`, Preview Pink `#de1d8d`, Ship Red `#ff5b4f`) exist ONLY to mark pipeline stages. Chroma is semantic, never ornamental.
- **Motion language:** Shadow-as-border (`0 0 0 1px rgba(0,0,0,.08)`), multi-layer shadow stacks with an inner `#fafafa` ring so cards "glow" from within. Depth is layered lightness, not blur.
- **Voice:** Terse imperative triads. "Develop. Preview. Ship." No adjectives about themselves anywhere.
- **Insider credibility:** The product is the demo — deploys render live on the homepage; grayscale logo trust bar; the same Geist/mono voice in marketing as in the CLI, so the site feels like documentation written by the infra itself.

### CROSS-CUTTING DNA (what all three share)
1. **One accent, total discipline.** Chroma is functional/semantic; everything else is neutral.
2. **Typography IS the brand.** A distinctive sans or mono, extreme tracking, an unusual weight (510), OpenType features treated as identity — not a stock font at default settings.
3. **Machine-truth artifacts.** Seeds, `FIG` numbers, real product data, live demos embedded in marketing. The site exposes its own internals.
4. **Compression-vs-void tension.** Dense, tight type sitting inside vast empty space.
5. **Voice = short declarative sentences.** No hype adjectives; ideology and numbers allowed.
6. **Insider credibility comes from specificity:** exact latencies, exact customer names, exact jargon used casually, provenance shown openly.

---

## PART 2 — THE DIRECTION FOR SICCE

### Concept: **NADI (नाडी) — "The pulse under the hospital."**

A **clinical-instrument** identity: the site is art-directed like a modern patient monitor / ICU instrument stack (Masimo, GE Carescape, Apple-clinical hardware), not like a website about one. Light-dominant sterile surfaces (kills both the dark-SaaS cliché AND the old paper-slip world), inverted only for "monitor glass" panels where the product lives. The unifying metaphor: SICCE is the hospital's **vital-signs monitor for language** — messy Hinglish in, structured FHIR out, rendered as a living trace.

Why it wins for EMR/HIS CTOs: instruments are the most trusted objects in a hospital. This direction borrows their authority (calibration marks, status LEDs, tabular numerics, alarm semantics) while the bilingual type + Hinglish demos prove — visibly — that this engine was built *for Indian clinical reality*, not localized into it.

#### Palette (hex)
| Token | Hex | Role |
|---|---|---|
| Sterile White | `#F4F5F1` | Page canvas (warm-neutral, not clinical blue-white) |
| Instrument Panel | `#E8EAE4` | Cards, sections |
| Graphite Ink | `#15181B` | Primary text |
| Monitor Glass | `#0B100E` | Inverted "device screen" panels only (hero, live demos) |
| **Phosphor Green** | `#19E68C` | THE single accent: trace line, live data, CTAs |
| Alarm Coral | `#FF4B3E` | Functional only — unmapped-term alerts, errors |
| Signal Amber | `#FFB000` | Functional only — warnings, review-needed states |

Discipline rule (stolen from Linear/Vercel): green = alive/translated; amber = needs review; coral = failed mapping. Chroma is always semantic. Never decorative.

#### Type stack
- **Display:** Space Grotesk (600/700, tracking −2% to −4% at display sizes) — geometric, slightly condensed, instrument-panel engraved feel.
- **Body/UI:** IBM Plex Sans **paired with IBM Plex Sans Devanagari as co-primary** — Devanagari is never a fallback or decoration; headlines run bilingual (Latin + देवनागरी echo line).
- **Data/code:** IBM Plex Mono (tabular figures) for all codes, latencies, FHIR payloads, calibration labels.
- Micro-labels: Plex Mono 11–12px UPPERCASE with wide tracking — "TRACE 04 // SNOMED 195967001" style captions replace Linear's `FIG` convention.

#### Signature interaction: **THE TRACE**
A continuous ECG-style oscilloscope line runs through the entire site. Wherever a demo appears, messy Hinglish text streams across the left of a Monitor Glass panel and the trace converts it segment-by-segment into clean coded output on the right: each successful SNOMED resolution fires a blip on the trace + a counter tick; ambiguous terms flash amber ("review"); untranslatables hit coral. Latency is displayed live (`p95 · 148ms`). Site-wide, a resting heartbeat (~72 bpm) pulses subtly beneath section headers. The product's core act — translation under pressure — becomes the visual identity.

#### Hero moment
Full-viewport **Monitor Glass panel** framed like a bedside device bezel (calibration ticks, status LEDs, `NADI v2.x` etched label). Top strip = hospital-board counters: bundles emitted today · ABDM linkages live · p95 latency. Left column streams real de-identified discharge snippets — *"patient ko 2 din se fever hai, BP 150/90, Metformin 500mg BD continue karein"* — while the right builds the FHIR R4 bundle JSON live, SNOMED codes stamping in with trace blips. Headline, bilingual:
> **The hospital speaks. SICCE translates.**
> **अस्पताल बोलता है। SICCE समझता है।**

Supporting copy register (instrument-manual brevity + numbers): "Garbage in. FHIR out." / "We read what doctors actually write." / "Hinglish → SNOMED CT → ABDM FHIR R4. p95 148ms." Internals exposed as credibility: real payload JSON, error-code taxonomy, dated changelog, M1/M2/M3 ABDM milestone badges — the Nous/Vercel "machine-truth" move applied to healthcare.
