class DemoDoctorAgent:
    """
    Offline/demo doctor agent:
    - Asks pre-defined questions for the patient.
    - Records patient answers.
    - Determines final diagnosis based on reported symptoms.
    """
    # Map diagnoses to relevant symptoms/questions
    DIAGNOSIS_QUESTIONS = {
        "Pneumonia": [
            "Are you experiencing chest pain?",
            "Are you experiencing shortness of breath?",
            "Do you have a fever?",
            "Do you have coughing?",
            "Any other symptoms I should know about?"
        ],
        "Myocardial infarction": [
            "Are you experiencing chest pain?",
            "Is the pain radiating to your left arm?",
            "Do you feel shortness of breath?",
            "Do you have sweating?",
            "Any other symptoms I should know about?"
        ],
        "Urinary tract infection": [
            "Are you experiencing painful urination?",
            "Do you have lower abdominal pain?",
            "Do you have fever?",
            "Any other symptoms I should know about?"
        ],
        "Intestinal obstruction": [
            "Are you experiencing abdominal pain?",
            "Do you have vomiting?",
            "Do you have constipation?",
            "Is your abdomen distended?",
            "Any other symptoms I should know about?"
        ],
        "Cerebral infarction": [
            "Are you experiencing facial droop?",
            "Are you experiencing weakness on one side?",
            "Are you having trouble speaking?",
            "Do you have confusion?",
            "Any other symptoms I should know about?"
        ]
    }

    def __init__(self, patient_info):
        self.patient_info = patient_info
        self.diagnosis = patient_info.get("diagnosis", "unknown")
        self.questions = self.DIAGNOSIS_QUESTIONS.get(self.diagnosis, [])
        self.curr_question_idx = 0
        self.answers = []

    def inference(self):
        """Return the next question, or a closing message if done."""
        if self.curr_question_idx >= len(self.questions):
            return "Thank you. I have enough information."
        question = self.questions[self.curr_question_idx]
        self.curr_question_idx += 1
        return question

    def record_answer(self, answer):
        """Store patient answer for final diagnosis evaluation."""
        self.answers.append(answer)

    def final_diagnosis(self, coverage: float, known_symptoms=None):
        """
        Determine final diagnosis based on:
        - coverage of explicitly asked symptoms
        - optionally all known symptoms (including volunteered)
        """
        if known_symptoms is None:
            known_symptoms = set()

        total_symptoms = set(self.patient_info.get("symptoms", []))

        # Consider all reported symptoms for diagnosis
        symptoms_reported = total_symptoms.intersection(known_symptoms)

        # Simple logic: if patient reported >=75% of all symptoms, HIGH confidence
        if len(symptoms_reported) / len(total_symptoms) >= 0.75:
            confidence = "HIGH"
        elif len(symptoms_reported) / len(total_symptoms) >= 0.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # Diagnosis is always the ground truth for demo purposes
        return self.patient_info.get("diagnosis", "Unknown"), confidence