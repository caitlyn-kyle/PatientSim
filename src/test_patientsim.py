import random
from agent.demo_patient_agent import DummyPatientAgent
from agent.demo_doctor_agent import DemoDoctorAgent
from data.data_retrieval import get_random_patient
from interviewer_evaluation import evaluate_question

# -------------------------------
# 1. Automated Demo Data Retrieval & Preprocessing
# -------------------------------
# demo_data.json is loaded and each patient is preprocessed to ensure consistency.
patient_profile = get_random_patient()
if not patient_profile:
    raise ValueError("[ERROR] No valid demo patient found.")

print("[INFO] Loaded and preprocessed demo patient:")
print(f"Patient ID: {patient_profile.get('hadm_id')}")
print(f"Diagnosis: {patient_profile.get('diagnosis')}")
print(f"Persona attributes: personality={patient_profile.get('personality')}, "
    f"CEFR={patient_profile.get('cefr')}, recall={patient_profile.get('recall_level')}, dazed={patient_profile.get('dazed_level')}")
print(f"Symptoms: {patient_profile.get('symptoms')}")

# Flatten patient info for doctor agent
patient_for_doctor = patient_profile.copy()
present_illness = patient_profile.get("present_illness", {})
patient_for_doctor["chief_complaint"] = present_illness.get("chief_complaint", "")
patient_for_doctor["hpi"] = present_illness.get("hpi", "")

# -------------------------------
# 2. Instantiate Agents 
# -------------------------------
# Offline demo allows controlled evaluation without API or processing delays
patient = DummyPatientAgent(patient_profile, verbose=True)
doctor = DemoDoctorAgent(patient_info=patient_for_doctor)

# -------------------------------
# 3. Tracking for Evaluation
# -------------------------------
explicitly_covered = []
volunteered = []

print("\n--- Starting Doctor-Patient Interview ---")
for _ in range(10):
    # Doctor generates next question
    question = doctor.inference()
    print(f"\nDoctor: {question}")

    # End interview if doctor concludes
    if "enough information" in question.lower():
        patient_answer = "Ok"
        print(f"Patient: {patient_answer}")
        break

    # -------------------------------
    # 4. Dynamic Patient Responses
    # -------------------------------
    # Patient responds to asked symptoms only; volunteers remaining symptoms probabilistically
    patient_answer = patient.inference(
        question,
        asked_symptoms=explicitly_covered + volunteered
    )
    print(f"Patient: {patient_answer}")

    doctor.record_answer(patient_answer)

    # -------------------------------
    # 5. Real-Time Question Evaluation
    # -------------------------------
    # Evaluates explicitly covered + volunteered symptoms in real-time
    eval_text, explicitly_covered, volunteered = evaluate_question(
        question,
        patient_profile,
        explicitly_covered,
        volunteered,
        patient_answer=patient_answer
    )
    print(f"Evaluation: {eval_text}")

# -------------------------------
# 6. Final Evaluation & Feedback
# -------------------------------
true_symptoms = set([s.lower() for s in patient_profile.get("symptoms", [])])
matched = set(explicitly_covered)
vol = set(volunteered)
all_reported = matched.union(vol)
missed = list(true_symptoms - all_reported)
coverage = len(matched) / len(true_symptoms) if true_symptoms else 0

# Final diagnosis confidence based on total coverage
diagnosis, confidence = doctor.final_diagnosis(coverage, known_symptoms=all_reported)

print("\n--- Interview Quality Summary ---")
print(f"Total symptoms: {len(true_symptoms)}")
print(f"Explicitly covered: {len(matched)}")
print(f"Volunteered: {len(vol)}")
print(f"Coverage: {int(coverage*100)}%")
print(f"Covered symptoms: {sorted(matched)}")
print(f"Volunteered symptoms: {sorted(vol)}")
print(f"Missed symptoms: {missed}")

# -------------------------------
# 7. Missed Symptoms & Follow-Up Suggestions
# -------------------------------
# Provides actionable learning feedback
if missed:
    print("\n--- Learning Feedback ---")
    for s in missed:
        print(f"Suggested follow-up: Ask about '{s}'")

# -------------------------------
# 8. Final Diagnosis Check
# -------------------------------
# Final diagnosis includes explicit + volunteered symptoms
print("\n--- Final Check ---")
print(f"Ground truth diagnosis: {patient_profile['diagnosis']}")
print(f"Doctor's final diagnosis: {diagnosis}")
print(f"Confidence: {confidence}")

