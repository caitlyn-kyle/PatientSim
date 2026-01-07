import random

# Probability that patient volunteers each remaining symptom
VOLUNTEER_PROB = 0.5  # 0 = never, 1 = always

class DummyPatientAgent:
    def __init__(self, patient_profile, verbose=False):
        self.patient_profile = patient_profile
        self.verbose = verbose
        self.volunteered_already = set()  # Track what was actually volunteered

    def inference(self, question, asked_symptoms=None):
        if asked_symptoms is None:
            asked_symptoms = []

        patient_symptoms = [s.lower() for s in self.patient_profile.get("symptoms", [])]
        question_lower = question.lower()

        # Doctor says enough information
        if "enough information" in question_lower:
            return "Ok"

        # Explicitly asked symptoms
        matched = [s for s in patient_symptoms if s in question_lower and s not in asked_symptoms]
        if matched:
            return "Yes, I am experiencing " + ", ".join(matched) + "."

        # "Any other symptoms"
        if "other symptoms" in question_lower:
            remaining = [s for s in patient_symptoms if s not in asked_symptoms and s not in self.volunteered_already]
            volunteered_now = []
            skipped_due_to_prob = []

            for s in remaining:
                if random.random() < VOLUNTEER_PROB:
                    volunteered_now.append(s)
                    self.volunteered_already.add(s)
                else:
                    skipped_due_to_prob.append(s)

            if volunteered_now:
                if self.verbose and skipped_due_to_prob:
                    print(f"Simulation: Patient chose NOT to volunteer {skipped_due_to_prob} due to probabilistic disclosure")
                return "Yes, I am experiencing " + ", ".join(volunteered_now) + "."
            else:
                return "No other symptoms."

        # Default negative response
        return "No, I am not experiencing that."
