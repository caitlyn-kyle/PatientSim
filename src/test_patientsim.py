import random
from agent.demo_patient_agent import DummyPatientAgent
from agent.demo_doctor_agent import DemoDoctorAgent
from data.data_retrieval import get_random_patient
from interviewer_evaluation import evaluate_question
# -------------------------------
# Load patient
# -------------------------------
patient_profile = get_random_patient()
if not patient_profile:
    raise ValueError("No valid demo patient found.")

# Flatten patient info for doctor
patient_for_doctor = patient_profile.copy()
present_illness = patient_profile.get("present_illness", {})
patient_for_doctor["chief_complaint"] = present_illness.get("chief_complaint", "")
patient_for_doctor["hpi"] = present_illness.get("hpi", "")

print("Flattened patient_for_doctor keys:", patient_for_doctor.keys())
print("Diagnosis field:", patient_for_doctor.get("diagnosis"))

# -------------------------------
# Instantiate agents
# -------------------------------
patient = DummyPatientAgent(patient_profile, verbose=True)
doctor = DemoDoctorAgent(patient_info=patient_for_doctor)

# -------------------------------
# Tracking for evaluation
# -------------------------------
explicitly_covered = []
volunteered = []

print("\n--- Starting Doctor-Patient Interview ---")
for _ in range(10):
    question = doctor.inference()
    print(f"\nDoctor: {question}")

    if "enough information" in question.lower():
        patient_answer = "Ok"
        print(f"Patient: {patient_answer}")
        break

    # Patient responds
    patient_answer = patient.inference(
        question,
        asked_symptoms=explicitly_covered + volunteered
    )
    print(f"Patient: {patient_answer}")

    doctor.record_answer(patient_answer)

    # Evaluate using actual patient answer
    eval_text, explicitly_covered, volunteered = evaluate_question(
        question,
        patient_profile,
        explicitly_covered,
        volunteered,
        patient_answer=patient_answer
    )
    print(f"Evaluation: {eval_text}")

# -------------------------------
# Final evaluation
true_symptoms = set([s.lower() for s in patient_profile.get("symptoms", [])])
matched = set(explicitly_covered)
vol = set(volunteered)
all_reported = matched.union(vol)
missed = list(true_symptoms - all_reported)
coverage = len(matched) / len(true_symptoms) if true_symptoms else 0

diagnosis, confidence = doctor.final_diagnosis(coverage, known_symptoms=all_reported)

print("\n--- Interview Quality Summary ---")
print(f"Total symptoms: {len(true_symptoms)}")
print(f"Explicitly covered: {len(matched)}")
print(f"Volunteered: {len(vol)}")
print(f"Coverage: {int(coverage*100)}%")
print(f"Covered symptoms: {sorted(matched)}")
print(f"Volunteered symptoms: {sorted(vol)}")
print(f"Missed symptoms: {missed}")

if missed:
    print("\n--- Learning Feedback ---")
    for s in missed:
        print(f"Suggested follow-up: Ask about '{s}'")

print("\n--- Final Check ---")
print(f"Ground truth diagnosis: {patient_profile['diagnosis']}")
print(f"Doctor's final diagnosis: {diagnosis}")
print(f"Confidence: {confidence}")
