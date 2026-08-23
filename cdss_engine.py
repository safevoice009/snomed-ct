"""
cdss_engine.py
Clinical Decision Support System (CDSS) for SICCE.
Performs real-time checks for:
1. Lethal / Major / Moderate Drug-Drug Interactions (DDI)
2. Patient Allergy Cross-Reactivity
3. Duplicate Therapy & High-Risk Prescribing Alerts
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("cdss_engine")

# Standard Clinical Pharmacology Drug-Drug Interaction Rules
KNOWN_DDI_RULES = [
    {
        "id": "DDI-001",
        "drugs": ["sildenafil", "nitroglycerin", "isosorbide", "nitrate"],
        "pair": ("sildenafil", "nitrate"),
        "severity": "CRITICAL",
        "title": "Severe Refractory Hypotension",
        "mechanism": "Co-administration of PDE5 inhibitors with nitrates potentiates cyclic GMP, leading to potentially fatal systemic vasodilation and profound hypotension.",
        "action": "Absolute Contraindication. Do not co-prescribe."
    },
    {
        "id": "DDI-002",
        "drugs": ["warfarin", "aspirin", "ibuprofen", "diclofenac", "aceclofenac", "combiflam", "voveran", "zerodol"],
        "pair": ("anticoagulant", "nsaid"),
        "severity": "CRITICAL",
        "title": "Major Hemorrhagic Bleeding Risk",
        "mechanism": "Concurrent use of anticoagulant (Warfarin) with NSAIDs significantly enhances gastrointestinal mucosal erosion and platelet inhibition.",
        "action": "Avoid combination. If analgesia needed, consider Paracetamol (Dolo 650) with gastroprotection."
    },
    {
        "id": "DDI-003",
        "drugs": ["enalapril", "ramipril", "telmisartan", "losartan", "spironolactone"],
        "pair": ("acei/arb", "potassium_sparing"),
        "severity": "WARNING",
        "title": "Hyperkalemia and Renal Dysfunction Risk",
        "mechanism": "Dual renin-angiotensin blockade or combination with potassium-sparing diuretics increases risk of severe hyperkalemia and acute kidney injury.",
        "action": "Monitor serum potassium and renal function within 7 days of starting therapy."
    },
    {
        "id": "DDI-004",
        "drugs": ["ciprofloxacin", "cifran", "budesonide", "budecort", "prednisolone", "dexamethasone"],
        "pair": ("fluoroquinolone", "corticosteroid"),
        "severity": "WARNING",
        "title": "Severe Tendonitis & Tendon Rupture Risk",
        "mechanism": "Concomitant use of fluoroquinolones with corticosteroids multiplies the incidence of Achilles tendonitis and tendon rupture.",
        "action": "Warn patient immediately to report heel pain or tendon swelling."
    },
    {
        "id": "DDI-005",
        "drugs": ["methotrexate", "aspirin", "ibuprofen", "diclofenac", "aceclofenac"],
        "pair": ("methotrexate", "nsaid"),
        "severity": "CRITICAL",
        "title": "Severe Methotrexate Toxicity & Pancytopenia",
        "mechanism": "NSAIDs decrease renal clearance of methotrexate, resulting in toxic serum levels and bone marrow suppression.",
        "action": "Strictly avoid high-dose NSAIDs during methotrexate cycles."
    },
    {
        "id": "DDI-006",
        "drugs": ["tramadol", "ultracet", "escitalopram", "sertraline", "fluoxetine", "paroxetine"],
        "pair": ("tramadol", "ssri"),
        "severity": "WARNING",
        "title": "Serotonin Syndrome & Seizure Risk",
        "mechanism": "Tramadol inhibits serotonin and norepinephrine reuptake; combined with SSRIs, it risks central serotonin toxicity and lowers seizure threshold.",
        "action": "Monitor for tremors, hyperreflexia, agitation, and diaphoresis."
    },
    {
        "id": "DDI-007",
        "drugs": ["clopidogrel", "clopilet", "omeprazole", "omez"],
        "pair": ("clopidogrel", "omeprazole"),
        "severity": "ADVISORY",
        "title": "Reduced Antiplatelet Efficacy",
        "mechanism": "Omeprazole inhibits CYP2C19, diminishing bioactivation of clopidogrel to its active antiplatelet metabolite.",
        "action": "Switch to Pantoprazole (Pan 40 / Pan-D), which has significantly lower CYP2C19 affinity."
    }
]

# Common Allergy Cross-Reactivity Rules
ALLERGY_RULES = [
    {
        "allergen": "penicillin",
        "triggers": ["penicillin", "amoxicillin", "ampicillin", "augmentin", "moxclav", "clavum"],
        "severity": "CRITICAL",
        "title": "Severe IgE-Mediated Anaphylaxis Risk",
        "message": "Patient has recorded Penicillin allergy. Beta-lactam antibiotic prescribed."
    },
    {
        "allergen": "aspirin",
        "triggers": ["aspirin", "ecosprin", "disprin", "ibuprofen", "diclofenac", "aceclofenac", "combiflam", "voveran", "zerodol"],
        "severity": "CRITICAL",
        "title": "NSAID-Exacerbated Respiratory Disease (NERD) / Bronchospasm Risk",
        "message": "Patient has recorded Aspirin/NSAID hypersensitivity. Cross-reactive COX-1 inhibitor prescribed."
    },
    {
        "allergen": "sulfa",
        "triggers": ["sulfamethoxazole", "bactrim", "septrin", "glimepiride"],
        "severity": "WARNING",
        "title": "Sulfonamide Cross-Reactivity Advisory",
        "message": "Patient has recorded Sulfa allergy. Prescribed drug contains sulfonamide structure."
    }
]

# Duplicate Therapy Categories
DUPLICATE_CATEGORIES = {
    "NSAID": ["ibuprofen", "diclofenac", "aceclofenac", "combiflam", "voveran", "zerodol", "aspirin", "ecosprin"],
    "Proton Pump Inhibitor": ["pantoprazole", "omeprazole", "rabeprazole", "pan 40", "pan-d", "omez", "omez-d", "razo-d"],
    "Antibiotic": ["augmentin", "azee", "cifran", "taxim-o", "monocef", "amoxicillin", "azithromycin", "ciprofloxacin", "cefixime"]
}


class CDSSEngine:
    """Clinical Decision Support Engine for checking drug interactions, allergies, and prescribing safety."""
    
    def __init__(self):
        pass

    def evaluate_safety(
        self, 
        medications: List[Dict[str, Any]], 
        patient_allergies: Optional[List[str]] = None,
        patient_conditions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Runs comprehensive clinical safety checks across all prescribed medications."""
        alerts = []
        patient_allergies = [a.strip().lower() for a in (patient_allergies or []) if a]
        patient_conditions = [c.strip().lower() for c in (patient_conditions or []) if c]

        # Extract normalized drug names
        drug_names = []
        for m in medications:
            display = m.get("display", "").lower()
            generic = m.get("generic_name", "").lower()
            orig = m.get("original_query", "").lower()
            drug_names.append((display, generic, orig, m))

        # 1. Drug-Drug Interactions Check
        for rule in KNOWN_DDI_RULES:
            matched_meds = []
            for d_tuple in drug_names:
                combined_text = f"{d_tuple[0]} {d_tuple[1]} {d_tuple[2]}"
                for drug_keyword in rule["drugs"]:
                    if drug_keyword in combined_text:
                        matched_meds.append(d_tuple[3].get("display") or d_tuple[0])
                        break
            
            # If two distinct interacting drug classes matched
            if len(matched_meds) >= 2:
                alerts.append({
                    "type": "DRUG_INTERACTION",
                    "severity": rule["severity"],
                    "title": rule["title"],
                    "involved_drugs": list(set(matched_meds)),
                    "mechanism": rule["mechanism"],
                    "recommended_action": rule["action"]
                })

        # 2. Allergy Cross-Reactivity Check
        for allergy in patient_allergies:
            for rule in ALLERGY_RULES:
                if rule["allergen"] in allergy:
                    for d_tuple in drug_names:
                        combined_text = f"{d_tuple[0]} {d_tuple[1]} {d_tuple[2]}"
                        for trigger in rule["triggers"]:
                            if trigger in combined_text:
                                alerts.append({
                                    "type": "ALLERGY_CONTRAINDICATION",
                                    "severity": rule["severity"],
                                    "title": rule["title"],
                                    "allergy": allergy,
                                    "prescribed_drug": d_tuple[3].get("display") or d_tuple[0],
                                    "mechanism": rule["message"],
                                    "recommended_action": "Discontinue medication and switch to non-cross-reactive alternative."
                                })

        # 3. Duplicate Therapy Check
        for cat_name, cat_drugs in DUPLICATE_CATEGORIES.items():
            matched_in_cat = []
            for d_tuple in drug_names:
                combined_text = f"{d_tuple[0]} {d_tuple[1]} {d_tuple[2]}"
                for drug_keyword in cat_drugs:
                    if drug_keyword in combined_text:
                        matched_in_cat.append(d_tuple[3].get("display") or d_tuple[0])
                        break
            if len(matched_in_cat) > 1 and cat_name != "Antibiotic": # Dual antibiotics can be intentional
                alerts.append({
                    "type": "DUPLICATE_THERAPY",
                    "severity": "WARNING",
                    "title": f"Duplicate {cat_name} Therapy Detected",
                    "involved_drugs": list(set(matched_in_cat)),
                    "mechanism": f"Patient is prescribed multiple agents in the {cat_name} pharmacological class, increasing risk of adverse events without added therapeutic benefit.",
                    "recommended_action": "Consolidate into a single optimized therapeutic regimen."
                })

        # 4. Disease-Drug Contraindication Check (e.g. Beta-blockers in Asthma)
        has_asthma = any("asthma" in c or "wheez" in c or "dama" in c for c in patient_conditions)
        if has_asthma:
            for d_tuple in drug_names:
                combined_text = f"{d_tuple[0]} {d_tuple[1]} {d_tuple[2]}"
                if "propranolol" in combined_text or "atenolol" in combined_text:
                    alerts.append({
                        "type": "DISEASE_CONTRAINDICATION",
                        "severity": "CRITICAL",
                        "title": "Beta-Blocker Contraindicated in Bronchial Asthma",
                        "involved_drugs": [d_tuple[3].get("display") or d_tuple[0]],
                        "mechanism": "Non-cardioselective beta-blockers trigger severe bronchoconstriction and life-threatening status asthmaticus.",
                        "action": "Switch to cardioselective beta-blocker or alternative antihypertensive class (e.g., Amlodipine / Telmisartan)."
                    })

        # Determine overall safety status
        has_critical = any(a["severity"] == "CRITICAL" for a in alerts)
        has_warning = any(a["severity"] == "WARNING" for a in alerts)
        
        if has_critical:
            safety_status = "CRITICAL_ALERTS_DETECTED"
        elif has_warning:
            safety_status = "WARNINGS_PRESENT"
        elif alerts:
            safety_status = "ADVISORIES_NOTED"
        else:
            safety_status = "CLEAR"

        return {
            "status": safety_status,
            "alerts_count": len(alerts),
            "alerts": alerts
        }
