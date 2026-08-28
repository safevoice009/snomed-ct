# Security & Responsible Disclosure Policy

Security, clinical data integrity, and privacy are foundational to the **SICCE** project.

---

## 🛡️ Reporting a Vulnerability

If you discover a security vulnerability or potential data safety risk within this repository:
1. Please **do not** report security vulnerabilities through public GitHub issues.
2. Send a detailed description of the issue to the maintainers via email at: `support@trochlea.online` (or open a Private Security Advisory on GitHub).
3. Include:
   - Steps to reproduce the issue.
   - Potential impact on clinical data or infrastructure.
   - Any suggested mitigations.

We will acknowledge receipt of your vulnerability report within 48 hours and work with you to patch the issue before public disclosure.

---

## 🔒 Security Best Practices in SICCE
- **No Hardcoded Keys**: API keys and secrets must never be committed to git. All authorization relies on environment variables (`API_KEYS`).
- **Cryptographic Hashing**: All authentication uses Argon2id for password verification.
- **Client-Side Data Sanitization**: PHI/PII de-identification is applied before sending clinical text to external model APIs.
- **DPDP Act 2023 Compliance**: Zero retention policy for clinical requests post-transformation.
