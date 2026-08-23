"""
webhook_handler.py
WhatsApp & Telephony Clinical Ingestion Bot Gateway.
Allows doctors and clinics to submit prescriptions or voice memos via WhatsApp Webhook
and receive instant, verified bilingual ABDM consultation summaries and patient dosage cards.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone

logger = logging.getLogger("webhook_handler")

class WhatsAppClinicalWebhook:
    """Processes incoming WhatsApp / Telephony clinical messages."""

    def format_whatsapp_reply(
        self,
        sender_phone: str,
        clinic_name: str,
        doctor_name: str,
        resolved_data: Dict[str, Any],
        cdss_data: Dict[str, Any],
        vernacular_schedules: list
    ) -> Dict[str, Any]:
        """Formats an enterprise WhatsApp clinical message with emojis, SNOMED IDs, and dosage schedules."""
        lines = []
        lines.append(f"🏥 *{clinic_name}*")
        lines.append(f"👨‍⚕️ *{doctor_name}*")
        lines.append("─────────────────────")
        
        # 1. Diagnoses & Complaints
        symptoms = resolved_data.get("symptoms", [])
        diagnoses = resolved_data.get("diagnoses", [])
        
        if diagnoses or symptoms:
            lines.append("📋 *CLINICAL FINDINGS (SNOMED CT):*")
            for d in diagnoses:
                lines.append(f"• *Dx:* {d.get('display') or d.get('original_query')} `[ID: {d.get('concept_id', 'Uncoded')}]`")
            for s in symptoms:
                lines.append(f"• *C/o:* {s.get('display') or s.get('original_query')} `[ID: {s.get('concept_id', 'Uncoded')}]`")
            lines.append("")

        # 2. Prescribed Medications
        meds = resolved_data.get("medications", [])
        if meds:
            lines.append("💊 *PRESCRIBED MEDICATIONS:*")
            for idx, m in enumerate(meds, 1):
                brand = m.get("display") or m.get("original_query", "Medication")
                dose = m.get("dose", "")
                freq = m.get("frequency", "")
                lines.append(f"{idx}. *{brand}* ({dose}) — {freq}")
            lines.append("")

        # 3. Patient Vernacular Dosage Guide (Hindi & Telugu)
        if vernacular_schedules:
            lines.append("🗣️ *PATIENT DOSAGE CARD (मरीज़ खुराक निर्देश):*")
            for v in vernacular_schedules[:3]:
                brand = v.get("brand_name", "")
                hi_inst = v.get("schedule", {}).get("hi", "")
                te_inst = v.get("schedule", {}).get("te", "")
                lines.append(f"• *{brand}*")
                if hi_inst:
                    lines.append(f"  🇮🇳 Hindi: _{hi_inst}_")
                if te_inst:
                    lines.append(f"  🇮🇳 Telugu: _{te_inst}_")
            lines.append("")

        # 4. CDSS Safety Alert
        alerts = cdss_data.get("alerts", [])
        if alerts:
            lines.append(f"⚠️ *CDSS SAFETY ALERT:* {alerts[0].get('title')}")
            lines.append(f"_{alerts[0].get('mechanism')}_")
            lines.append("")
        else:
            lines.append("🛡️ *CDSS Safety:* Zero drug-drug interactions detected.")
            lines.append("")

        lines.append("✅ *ABDM FHIR R4 Bundle Created*")
        lines.append(f"🕒 _Timestamp: {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}_")
        
        formatted_body = "\n".join(lines)
        
        return {
            "recipient": sender_phone,
            "message_body": formatted_body,
            "status": "QUEUED_FOR_DISPATCH"
        }
