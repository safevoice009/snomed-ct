# SICCE Website — Version 2 (Design Council Edition)

## Rules of engagement
- v1 (root index.html, "Rx Slip" editorial) is FROZEN. Do not touch it.
- v2 lives entirely in /static/v2/. Entry point: index.html
- Must be deployable as-is from /static/v2/index.html
- No AI-slop patterns: no purple gradients, no glassmorphism cards, no generic hero+3-cards+logos
- Target feeling: stepping inside a living hospital machine — a patient/doctor should FEEL the portal
- Single self-contained HTML (CDN libs allowed), mobile-graceful degradation
- Honesty laws apply to copy: every claim dated & true
- Live demo must hit /api/demo-parse (real production engine, no mock)
