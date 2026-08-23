"""
eval/run_eval.py
================
Clinical NLP & Terminology Evaluation Harness.

Per MASTER_DIRECTIVE.md Task 1.5:
- Runs pipeline over de-identified clinical notes in eval/notes.jsonl.
- Calculates Precision, Recall, and F1 per entity type (Symptoms, Diagnoses, Medications).
- Computes Sub-Metrics for Dosage & Frequency.
- Outputs timestamped JSON report in eval/results/ and displays summary table.
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Set

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


async def run_evaluation(notes_path: str = "eval/notes.jsonl") -> Dict[str, Any]:
    parser = ClinicalParser()
    
    if not os.path.exists(notes_path):
        print(f"Error: Evaluation dataset not found at {notes_path}")
        return {}

    cases = []
    with open(notes_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line.strip()))

    print(f"Loaded {len(cases)} evaluation clinical cases from {notes_path}.")

    symptom_tp, symptom_fp, symptom_fn = 0, 0, 0
    diagnosis_tp, diagnosis_fp, diagnosis_fn = 0, 0, 0
    med_name_tp, med_name_fp, med_name_fn = 0, 0, 0
    med_dose_tp, med_dose_fp, med_dose_fn = 0, 0, 0
    med_freq_tp, med_freq_fp, med_freq_fn = 0, 0, 0

    results_detail = []

    for case in cases:
        case_id = case.get("id", "unknown")
        raw_text = case.get("text_raw", "")
        gold = case.get("entities", {})

        # Run extraction
        pred = await parser.parse(raw_text)

        # 1. Evaluate Symptoms
        gold_symptoms = {normalize(s) for s in gold.get("symptoms", [])}
        pred_symptoms = {normalize(s) for s in pred.get("symptoms", [])}

        c_s_tp = len(gold_symptoms & pred_symptoms)
        c_s_fp = len(pred_symptoms - gold_symptoms)
        c_s_fn = len(gold_symptoms - pred_symptoms)

        symptom_tp += c_s_tp
        symptom_fp += c_s_fp
        symptom_fn += c_s_fn

        # 2. Evaluate Diagnoses
        gold_diag = {normalize(d) for d in gold.get("diagnoses", [])}
        pred_diag = {normalize(d) for d in pred.get("diagnoses", [])}

        c_d_tp = len(gold_diag & pred_diag)
        c_d_fp = len(pred_diag - gold_diag)
        c_d_fn = len(gold_diag - pred_diag)

        diagnosis_tp += c_d_tp
        diagnosis_fp += c_d_fp
        diagnosis_fn += c_d_fn

        # 3. Evaluate Medications
        gold_meds = gold.get("medications", [])
        pred_meds = pred.get("medications", [])

        # Match by brand name or generic name
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
                # Check dose
                if gm_dose and normalize(matched_pred.get("dose", "")) == gm_dose:
                    med_dose_tp += 1
                else:
                    med_dose_fn += 1
                # Check freq
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

        results_detail.append({
            "case_id": case_id,
            "gold": gold,
            "pred": pred
        })

    symptom_metrics = compute_metrics(symptom_tp, symptom_fp, symptom_fn)
    diagnosis_metrics = compute_metrics(diagnosis_tp, diagnosis_fp, diagnosis_fn)
    med_name_metrics = compute_metrics(med_name_tp, med_name_fp, med_name_fn)
    med_dose_metrics = compute_metrics(med_dose_tp, med_dose_fp, med_dose_fn)
    med_freq_metrics = compute_metrics(med_freq_tp, med_freq_fp, med_freq_fn)

    macro_f1 = round((symptom_metrics["f1"] + diagnosis_metrics["f1"] + med_name_metrics["f1"]) / 3, 4)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(cases),
        "macro_f1": macro_f1,
        "metrics": {
            "symptoms": symptom_metrics,
            "diagnoses": diagnosis_metrics,
            "medications_entity": med_name_metrics,
            "medications_dose": med_dose_metrics,
            "medications_frequency": med_freq_metrics
        },
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
    print("\n==========================================================================")
    print("           SICCE CLINICAL EXTRACTION EVALUATION REPORT                    ")
    print("==========================================================================")
    print(f" Total Notes Evaluated: {len(cases)}")
    print(f" Macro F1 Score:        {macro_f1:.4f}")
    print("--------------------------------------------------------------------------")
    print(f" {'Entity Category':<25} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Target F1':<10}")
    print("--------------------------------------------------------------------------")
    print(f" {'Clinical Diagnoses':<25} | {diagnosis_metrics['precision']:<10.4f} | {diagnosis_metrics['recall']:<10.4f} | {diagnosis_metrics['f1']:<10.4f} | {'>= 0.90':<10}")
    print(f" {'Medication Entities':<25} | {med_name_metrics['precision']:<10.4f} | {med_name_metrics['recall']:<10.4f} | {med_name_metrics['f1']:<10.4f} | {'>= 0.92':<10}")
    print(f" {'Clinical Symptoms':<25} | {symptom_metrics['precision']:<10.4f} | {symptom_metrics['recall']:<10.4f} | {symptom_metrics['f1']:<10.4f} | {'>= 0.88':<10}")
    print(f" {'Medication Dosage':<25} | {med_dose_metrics['precision']:<10.4f} | {med_dose_metrics['recall']:<10.4f} | {med_dose_metrics['f1']:<10.4f} | {'-':<10}")
    print(f" {'Medication Frequency':<25} | {med_freq_metrics['precision']:<10.4f} | {med_freq_metrics['recall']:<10.4f} | {med_freq_metrics['f1']:<10.4f} | {'-':<10}")
    print("==========================================================================")
    print(f" Detailed Report Saved: {out_path}\n")

    return report


if __name__ == "__main__":
    asyncio.run(run_evaluation())
