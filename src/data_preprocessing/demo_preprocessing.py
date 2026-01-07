import random

DEFAULT_PERSONALITY = "plain"
DEFAULT_CEFR = "B"
DEFAULT_RECALL = "normal"
DEFAULT_DAZED = "normal"

# Mapping diagnosis → actual patient symptoms
SYMPTOMS_BY_DIAGNOSIS = {
    "pneumonia": ["cough", "fever", "shortness of breath"],
    "urinary tract infection": ["burning", "pain", "frequency"],
    "myocardial infarction": ["chest pain", "radiating", "arm", "sweating", "breath"],
    "intestinal obstruction": ["vomiting", "constipation", "distension", "abdominal pain"],
    "cerebral infarction": ["facial droop", "confusion", "weakness", "slurred speech"]
}

def demo_preprocess_patient_record(patient: dict):
    """
    Preprocess demo patient:
    - Fill missing persona / CEFR / recall / dazed defaults
    - Generate CEFR-specific words for communication
    - Assign patient-specific symptoms for logical responses
    """

    # Required fields check
    required = ["hadm_id", "diagnosis", "age", "sex"]
    for r in required:
        if r not in patient:
            print(f"[WARN] Missing field {r}, skipping patient")
            return None

    # Persona defaults 
    patient["personality"] = patient.get("personality", DEFAULT_PERSONALITY)
    patient["cefr"] = patient.get("cefr", DEFAULT_CEFR)
    patient["recall_level"] = patient.get("recall_level", DEFAULT_RECALL)
    patient["dazed_level"] = patient.get("dazed_level", DEFAULT_DAZED)

    # CEFR word mapping 
    cefr_vocab = {
        "A": ["pain", "feel", "bad", "hurt", "ache"],
        "B": ["pressure", "burning", "sharp", "tight", "throbbing"],
        "C": ["radiating", "intermittent", "progressive", "intense", "stabbing"]
    }

    med_vocab = {
        "A": ["pain", "urine", "burning", "ache"],
        "B": ["infection", "pressure", "headache", "cough", "fever"],
        "C": ["myocardial infarction", "photophobia", "vomiting", "distension"]
    }

    # Pre-fill all levels for safety
    for level in ["A", "B", "C"]:
        patient[f"cefr_{level}1"] = ", ".join(random.sample(cefr_vocab[level], 2))
        patient[f"cefr_{level}2"] = ", ".join(random.sample(cefr_vocab[level], 2))
        patient[f"med_{level}"] = ", ".join(random.sample(med_vocab[level], 2))

    # Key info
    patient["chief_complaint"] = patient["present_illness"].get("chief_complaint", patient["diagnosis"])
    patient["history_present_illness"] = patient["present_illness"].get("hpi", f"The patient reports {patient['diagnosis']}.")

    # Assign patient-specific symptoms
    patient["symptoms"] = SYMPTOMS_BY_DIAGNOSIS.get(patient["diagnosis"].lower(), [])

    # Final shape
    patient["split"] = "demo"

    return patient
