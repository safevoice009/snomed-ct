# SICCE Clinical Accuracy Benchmark Report
**Evaluation Harness**: `eval/run_eval.py`  
**Dataset Reference**: `eval/notes.jsonl` (De-identified & Synthetic Gold Standard Cases)  
**Date of Run**: August 23, 2026  
**Status**: 🟢 **VERIFIED & REPRODUCIBLE**

---

## 📊 Summary Extraction Metrics

| Clinical Entity Category | Precision | Recall | F1-Score | Target Benchmark | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Medication Entities (Brand & Generic)** | **0.9091** | **1.0000** | **0.9524** | $\ge 0.92$ | 🟢 **PASSED** |
| **Medication Dosage Extraction** | **1.0000** | **0.9000** | **0.9474** | - | 🟢 **HIGH ACCURACY** |
| **Medication Frequency Extraction** | **1.0000** | **0.9000** | **0.9474** | - | 🟢 **HIGH ACCURACY** |
| **Clinical Symptoms** | **0.8571** | **0.6667** | **0.7500** | $\ge 0.88$ | 🟡 In-Progress (Refining) |
| **Clinical Diagnoses** | **0.7500** | **0.5000** | **0.6000** | $\ge 0.90$ | 🟡 In-Progress (Refining) |

**Overall Macro F1**: **0.7675**

---

## 🔬 Benchmark Methodology

1. **Entity Normalization**: Case-insensitive text normalization, stripping trailing punctuation, and mapping standard dosage patterns (`OD`, `BD`, `TDS`, `QID`, `SOS`, `HS`).
2. **Deterministic Precedence**:
   - Step 1: SQLite FTS5 exact brand/concept matching.
   - Step 2: Synonym/description matching (e.g. `APD` $\rightarrow$ Acid peptic disease, `saas phoolna` $\rightarrow$ Dyspnea on exertion).
   - Step 3: Unresolved logging to `logs/unresolved_terms.jsonl` without hallucinating or guessing.
3. **Reproducibility Command**:
   ```powershell
   uv run python eval/run_eval.py
   ```
