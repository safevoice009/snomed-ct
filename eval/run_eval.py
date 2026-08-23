"""
eval/run_eval.py
================
Clinical NLP & Terminology Evaluation Harness.

Per MASTER_DIRECTIVE.md Task 1.5 & Task A (Honesty Enforcement):
- Splits evaluation between REAL clinical notes and SYNTHETIC test cases.
- Emits prominent honesty warning when only synthetic notes are present.
- Calculates Precision, Recall, and F1 per entity type (Symptoms, Diagnoses, Medications).
- Computes Sub-Metrics for Dosage & Frequency.
- Outputs timestamped JSON report in eval/results/ and displays summary table.
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Set, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from nlp_parser import ClinicalParser


def normalize(s: str) -> str:
    if not s:
        return ""
    return s.strip().lower().replace("-", " ").replace(".", "")


def compute_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
    recall = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if fp == 0 else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn
    }


async def evaluate_subset(parser: ClinicalParser, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not cases:
        return {
            "total_cases": 0,
            "macro_f1": 0.0,
            "metrics": {
                "symptoms": compute_metrics(0, 0, 0),
                "diagnoses": compute_metrics(0, 0, 0),
                "medications_entity": compute_metrics(0, 0, 0),
                "medications_dose": compute_metrics(0, 0, 0),
                "medications_frequency": compute_metrics(0, 0, 0)
            }
        }

    symptom_tp, symptom_fp, symptom_fn = 0, 0, 0
    diagnosis_tp, diagnosis_fp, diagnosis_fn = 0, 0, 0
    med_name_tp, med_name_fp, med_name_fn = 0, 0, 0
    med_dose_tp, med_dose_fp, med_dose_fn = 0, 0, 0
    med_freq_tp, med_freq_fp, med_freq_fn = 0, 0, 0

    for case in cases:
        raw_text = case.get("text_raw", "")
        gold = case.get("entities", {})

        pred = await parser.parse(raw_text)

        # 1. Symptoms
        gold_symptoms = {normalize(s) for s in gold.get("symptoms", [])}
        pred_symptoms = {normalize(s) for s in pred.get("symptoms", [])}
        symptom_tp += len(gold_symptoms & pred_symptoms)
        symptom_fp += len(pred_symptoms - gold_symptoms)
        symptom_fn += len(gold_symptoms - pred_symptoms)

        # 2. Diagnoses
        gold_diag = {normalize(d) for d in gold.get("diagnoses", [])}
        pred_diag = {normalize(d) for d in pred.get("diagnoses", [])}
        diagnosis_tp += len(gold_diag & pred_diag)
        diagnosis_fp += len(pred_diag - gold_diag)
        diagnosis_fn += len(gold_diag - pred_diag)

        # 3. Medications
        gold_meds = gold.get("medications", [])
        pred_meds = pred.get("medications", [])

        for gm in gold_meds:
            gm_brand = normalize(gm.get("brand_name", ""))
            gm_gen = normalize(gm.get("generic_name", ""))
            gm_dose = normalize(gm.get("dose", ""))
            gm_freq = normalize(gm.get("frequency", ""))

            matched_pred = None
            for pm in pred_meds:
                pm_brand = normalize(pm.get("brand_name", ""))
                pm_gen = normalize(pm.get("generic_guess", ""))
                if (gm_brand and gm_brand in pm_brand) or (gm_gen and gm_gen in pm_gen) or (pm_brand and pm_brand in gm_brand):
                    matched_pred = pm
                    break

            if matched_pred:
                med_name_tp += 1
                if gm_dose and normalize(matched_pred.get("dose", "")) == gm_dose:
                    med_dose_tp += 1
                else:
                    med_dose_fn += 1
                if gm_freq and normalize(matched_pred.get("frequency", "")) == gm_freq:
                    med_freq_tp += 1
                else:
                    med_freq_fn += 1
            else:
                med_name_fn += 1
                if gm_dose: med_dose_fn += 1
                if gm_freq: med_freq_fn += 1

        for pm in pred_meds:
            pm_brand = normalize(pm.get("brand_name", ""))
            pm_gen = normalize(pm.get("generic_guess", ""))
            if not any((normalize(gm.get("brand_name", "")) in pm_brand or normalize(gm.get("generic_name", "")) in pm_gen) for gm in gold_meds):
                med_name_fp += 1

    symptom_metrics = compute_metrics(symptom_tp, symptom_fp, symptom_fn)
    diagnosis_metrics = compute_metrics(diagnosis_tp, diagnosis_fp, diagnosis_fn)
    med_name_metrics = compute_metrics(med_name_tp, med_name_fp, med_name_fn)
    med_dose_metrics = compute_metrics(med_dose_tp, med_dose_fp, med_dose_fn)
    med_freq_metrics = compute_metrics(med_freq_tp, med_freq_fp, med_freq_fn)

    macro_f1 = round((symptom_metrics["f1"] + diagnosis_metrics["f1"] + med_name_metrics["f1"]) / 3, 4)

    return {
        "total_cases": len(cases),
        "macro_f1": macro_f1,
        "metrics": {
            "symptoms": symptom_metrics,
            "diagnoses": diagnosis_metrics,
            "medications_entity": med_name_metrics,
            "medications_dose": med_dose_metrics,
            "medications_frequency": med_freq_metrics
        }
    }


async def run_evaluation(notes_path: str = "eval/notes.jsonl") -> Dict[str, Any]:
    parser = ClinicalParser()
    
    if not os.path.exists(notes_path):
        print(f"Error: Evaluation dataset not found at {notes_path}")
        return {}

    all_cases = []
    with open(notes_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_cases.append(json.loads(line.strip()))

    real_cases = [c for c in all_cases if c.get("source") == "real"]
    synthetic_cases = [c for c in all_cases if c.get("source") != "real"]

    print(f"\nLoaded {len(all_cases)} total notes ({len(real_cases)} REAL, {len(synthetic_cases)} SYNTHETIC).")

    # Run separate evaluations
    real_results = await evaluate_subset(parser, real_cases)
    synthetic_results = await evaluate_subset(parser, synthetic_cases)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_notes": len(all_cases),
            "real_notes_count": len(real_cases),
            "synthetic_notes_count": len(synthetic_cases),
            "real_notes_evaluated": len(real_cases) > 0,
            "certification_status": "REAL_DATA_EVALUATED" if len(real_cases) >= 200 else "PENDING_FOUNDER_REAL_DATA"
        },
        "real_metrics": real_results,
        "synthetic_metrics": synthetic_results,
        "target_f1": {
            "diagnoses": 0.90,
            "medications": 0.92,
            "symptoms": 0.88
        }
    }

    # Save results to file
    out_dir = os.path.join(PROJECT_ROOT, "eval", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"eval_report_{timestamp}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print Table
    if len(real_cases) == 0:
        print("\n" + "=" * 80)
        print(" [!] SYNTHETIC BENCHMARK NOTICE (Law #4 / Truth-in-Docs):")
        print("     Parser rules were tuned against these synthetic notes (circular test).")
        print("     This is an internal plumbing test, NOT certification-grade accuracy.")
        print("     Real-note targets per MASTER_DIRECTIVE Task 1.5 are NOT yet met.")
        print("     Status: Awaiting 200+ real de-identified notes from founder.")
        print("=" * 80)
    else:
        print("\n==========================================================================")
        print(f"           SICCE REAL CLINICAL DATA EVALUATION ({len(real_cases)} Notes)")
        print("==========================================================================")
        print(f" Macro F1 Score: {real_results['macro_f1']:.4f}")
        rm = real_results["metrics"]
        print(f" {'Clinical Diagnoses':<25} | {rm['diagnoses']['precision']:<10.4f} | {rm['diagnoses']['recall']:<10.4f} | {rm['diagnoses']['f1']:<10.4f} | {'>= 0.90':<10}")
        print(f" {'Medication Entities':<25} | {rm['medications_entity']['precision']:<10.4f} | {rm['medications_entity']['recall']:<10.4f} | {rm['medications_entity']['f1']:<10.4f} | {'>= 0.92':<10}")
        print(f" {'Clinical Symptoms':<25} | {rm['symptoms']['precision']:<10.4f} | {rm['symptoms']['recall']:<10.4f} | {rm['symptoms']['f1']:<10.4f} | {'>= 0.88':<10}")
        print("=" * 80)

    print("\n--------------------------------------------------------------------------")
    print(f" SYNTHETIC DEVELOPER-PLUMBING METRICS ({len(synthetic_cases)} Cases)")
    print("--------------------------------------------------------------------------")
    sm = synthetic_results["metrics"]
    print(f" Macro F1 (Synthetic):  {synthetic_results['macro_f1']:.4f}")
    print(f" {'Entity Category':<25} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Target F1':<10}")
    print("--------------------------------------------------------------------------")
    print(f" {'Clinical Diagnoses':<25} | {sm['diagnoses']['precision']:<10.4f} | {sm['diagnoses']['recall']:<10.4f} | {sm['diagnoses']['f1']:<10.4f} | {'>= 0.90 (Real)':<10}")
    print(f" {'Medication Entities':<25} | {sm['medications_entity']['precision']:<10.4f} | {sm['medications_entity']['recall']:<10.4f} | {sm['medications_entity']['f1']:<10.4f} | {'>= 0.92 (Real)':<10}")
    print(f" {'Clinical Symptoms':<25} | {sm['symptoms']['precision']:<10.4f} | {sm['symptoms']['recall']:<10.4f} | {sm['symptoms']['f1']:<10.4f} | {'>= 0.88 (Real)':<10}")
    print(f" {'Medication Dosage':<25} | {sm['medications_dose']['precision']:<10.4f} | {sm['medications_dose']['recall']:<10.4f} | {sm['medications_dose']['f1']:<10.4f} | {'-':<10}")
    print(f" {'Medication Frequency':<25} | {sm['medications_frequency']['precision']:<10.4f} | {sm['medications_frequency']['recall']:<10.4f} | {sm['medications_frequency']['f1']:<10.4f} | {'-':<10}")
    print("==========================================================================")
    print(f" Detailed Report Saved: {out_path}\n")

    return report


if __name__ == "__main__":
    asyncio.run(run_evaluation())
