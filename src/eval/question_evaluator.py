class QuestionEvaluator:
    def __init__(self, patient_profile, config):
        self.patient_profile = patient_profile
        self.history = []
        self.covered_items = set()
        self.volunteered = set()
        self.symptoms = self.extract_positive_symptoms()
        self.predicted_diagnoses = []  # store top-5 diagnoses


    SYMPTOM_NORMALIZATION = {
        "sob": ["shortness of breath", "difficulty breathing", "dyspnea"],
        "vomiting": [
            "throwing up",
            "vomit",
            "nbnb vomiting",
            "projectile vomiting",
            "vomiting x",
            "episodes of vomiting",
        ],
        "nausea": ["feeling sick", "queasy", "sick to my stomach"],
        "abdominal pain": ["stomach pain", "stomach hurts", "abd pain", "belly pain"],
        "diarrhea": ["loose stools", "loose watery stools", "watery stool"],
        "abdominal distention": ["abd distention", "bloating", "swollen stomach"],
    }  # add more

    def symptom_matches(self, text, symptom):
        text = text.lower()

        # Direct base match
        if symptom in text:
            return True

        # Check variant matches
        for variant in self.SYMPTOM_NORMALIZATION.get(symptom, []):
            if variant in text:
                return True

        # Loose word-level fallback
        symptom_words = symptom.split()
        if any(word in text for word in symptom_words):
            return True

        return False

    def normalize_symptom(self, symptom_text):
        symptom_text = symptom_text.lower().strip()

        for base, variants in self.SYMPTOM_NORMALIZATION.items():
            # Exact match
            if symptom_text == base:
                return base

            # Variant match
            for variant in variants:
                if variant in symptom_text:
                    return base

        return symptom_text

    def extract_positive_symptoms(self):
        positive = self.patient_profile.get("present_illness_positive", "")

        if not positive:
            return []

        raw_items = positive.split(";")
        cleaned = []

        for item in raw_items:
            symptom = item.split("(")[0].strip().lower()

            # Normalize to base symptom
            normalized = self.normalize_symptom(symptom)
            if normalized:
                cleaned.append(normalized)

        # Remove duplicates
        return list(set(cleaned))

    def extract_diagnosis(self):
        correct_diagnosis = self.patient_profile.get("diagnosis", "")
        return correct_diagnosis

    def evaluate(self, question, patient_answer=""):
        # Track coverage before each question
        covered_before = set(self.covered_items)
        volunteered_before = set(self.volunteered)

        # Update coverage and get per-question coverage
        per_question_coverage = self.score_coverage(question, patient_answer)

        # Newly covered symptoms this turn
        newly_covered = len(self.covered_items) - len(covered_before)
        newly_volunteered = len(self.volunteered) - len(volunteered_before)

        # Fraction of total symptoms addressed this turn
        per_question_coverage_fraction = (
            (newly_covered + newly_volunteered) / len(self.symptoms)
            if self.symptoms else 0
        )

        relevance = self.score_relevance(question, patient_answer)
        structure = self.score_structure(question) * 100
        history = self.score_history(question) * 100

        total_score = int(round(
            0.4 * (per_question_coverage_fraction * 100) +
            0.4 * relevance +
            0.15 * structure +
            0.05 * history
        ))

        result = {
            "coverage_score": per_question_coverage,
            "relevance": relevance,
            "structure": structure,
            "history": history,
            "total_score": total_score,
        }

        # Store history internally
        self.history.append({
            "coverage_score": per_question_coverage,
            "relevance": relevance,
            "structure": structure,
            "history": history,
            "total_score": total_score,
        })

        # Print only the single line per turn
        print(
            f"Coverage: {int(per_question_coverage*100)}%, Relevance: {relevance}"
        )

        return {
            "coverage_score": per_question_coverage,
            "relevance": relevance,
            "structure": structure,
            "history": history,
            "total_score": total_score,
        }

    def score_coverage(self, question, patient_answer=""):
        question_lower = question.lower()
        answer_lower = patient_answer.lower().strip()

        # Determine if this is a general 'anything else?' question
        general_question = any(
            phrase in question_lower
            for phrase in ["any other", "anything else", "other symptoms", "additional symptoms"]
        )

        # Explicit coverage from the question
        for symptom in self.symptoms:
            if self.symptom_matches(question_lower, symptom):
                self.covered_items.add(symptom)
        
        # Volunteered coverage from general questions or patient answers
        for symptom in self.symptoms:
            if self.symptom_matches(answer_lower, symptom):
                # If not explicitly covered yet, count as volunteered
                if symptom not in self.covered_items:
                    self.volunteered.add(symptom)
        
        # Return fraction of total symptoms addressed this turn
        newly_covered = len(self.covered_items)
        newly_volunteered = len(self.volunteered)
        coverage_fraction = (
            (newly_covered + newly_volunteered) / len(self.symptoms) if self.symptoms else 0
        )

        # Optional debug text
        text = (
            f"Coverage: {int(coverage_fraction*100)}% | "
            f"explicitly covered: {list(self.covered_items)} | "
            f"volunteered: {list(self.volunteered)}"
        )

        return coverage_fraction

    def score_relevance(self, question, patient_answer=""):
        question_lower = question.lower()
        
        # Direct symptom relevance
        for symptom in self.symptoms:
            if self.symptom_matches(question_lower, symptom):
                return 100  # directly asks about the symptom
        
        # General symptom/clinical terms
        GENERAL_CLINICAL_TERMS = [
            "pain", "fever", "vomit", "nausea", "stool", "blood", "urine", "symptom"
        ]
        if any(term in question_lower for term in GENERAL_CLINICAL_TERMS):
            return 70
        
        # Contextual/clinical relevance: diet, exposure, travel, lifestyle
        CONTEXTUAL_TERMS = [
            "diet", "food", "water", "travel", "exposure", "occupation", "recent", "chronic", "medication", "allergy", "lifestyle", "smoke", "alcohol", "drug", "family history", "drink"
        ]
        if any(term in question_lower for term in CONTEXTUAL_TERMS):
            return 70
        
        # Optional: if patient answer mentions a key symptom not asked yet
        if patient_answer:
            for symptom in self.symptoms:
                if self.symptom_matches(patient_answer.lower(), symptom):
                    return 60  # relevant because it elicited useful info
        
        return 50

    def score_structure(self, question):
        q = question.lower().strip()
        score = 0.5  # baseline

        # Open-ended questions
        if any(
            phrase in q
            for phrase in ["can you describe", "tell me about", "how did", "describe"]
        ):
            score += 0.3

        # Closed yes/no
        elif any(phrase in q for phrase in ["do you", "is there", "have you"]):
            score += 0.1

        # Must end with one question mark
        if q.endswith("?"):
            score += 0.1

        # Penalize compound questions
        if q.count("?") > 1:
            score -= 0.2

        return round(min(max(score, 0), 1), 2)

    def score_history(self, question):
        q = question.lower()

        if any(
            word in q
            for word in [
                "when",
                "since",
                "previous",
                "previously",
                "history",
                "recently",
                "start",
                "started",
            ]
        ):
            return 1.0

        if any(
            word in q
            for word in ["ever", "experience", "experienced", "lifestyle", "family"]
        ):
            return 0.8

        return 0.0
    
    def get_predicted_diagnoses(self, diagnoses):
        self.predicted_diagnoses = diagnoses
        for diag in self.predicted_diagnoses:
            print(f"Predicted Diagnoses: {diag}")
        return self.predicted_diagnoses

    def generate_feedback(self):
        if not self.history:
            return {}

        # Weights for the total score calculation
        weight_coverage = 0.4
        weight_relevance = 0.4
        weight_structure = 0.15
        weight_history = 0.05

        num_questions = len(self.history)
        max_per_question = 100  # max per question

        # Totals for normalization
        total_weighted_score = 0
        total_coverage_score = 0
        total_relevance_score = 0
        total_structure_score = 0
        total_history_score = 0

        for q in self.history:
            cov = q["coverage_score"] * 100
            rel = q["relevance"]
            struct = q["structure"]
            hist = q["history"]

            total_coverage_score += cov
            total_relevance_score += rel
            total_structure_score += struct
            total_history_score += hist

            total_weighted_score += (
                weight_coverage * cov +
                weight_relevance * rel +
                weight_structure * struct +
                weight_history * hist
            )

        # Normalize totals to 0–100 scale
        weighted_score_percent = total_weighted_score / (num_questions * max_per_question) * 100
        relevance_percent_total = total_relevance_score / (num_questions * 100) * 100
        structure_percent_total = total_structure_score / (num_questions * 100) * 100
        history_percent_total = total_history_score / (num_questions * 100) * 100

        coverage_percent = len(self.covered_items | self.volunteered) / len(self.symptoms) if self.symptoms else 0
        missed = set(self.symptoms) - self.covered_items - self.volunteered

        # Summary print
        print("==== Interview Evaluation Summary ====")
        self.get_predicted_diagnoses(self.predicted_diagnoses)
        print(f"Overall Weighted Score: {weighted_score_percent:.1f}%")
        print(f"Relevance Score (normalized): {relevance_percent_total:.1f}%")
        print(f"Structure Score (normalized): {structure_percent_total:.1f}%")
        print(f"History Score (normalized): {history_percent_total:.1f}%")
        print(f"Overall Coverage of Symptoms: {coverage_percent*100:.0f}%")
        print(f"Covered Symptoms: {self.covered_items}")
        print(f"Volunteered Symptoms: {self.volunteered}")
        print(f"Missed Symptoms: {missed}")
        print(f"Correct Diagnosis: {self.extract_diagnosis()}\n")

        print("Per-turn breakdown:")
        for i, turn in enumerate(self.history, 1):
            print(
                f"Q{i}: Coverage {int(turn['coverage_score']*100)}%, "
                f"Relevance {int(turn['relevance'])}%, "
                f"Structure {int(turn['structure'])}%, "
                f"History {int(turn['history'])}%, "
                f"Total {turn['total_score']}"
            )

        feedback = {
            "weighted_score_percent": round(weighted_score_percent, 1),
            "relevance_percent_total": round(relevance_percent_total, 1),
            "structure_percent_total": round(structure_percent_total, 1),
            "history_percent_total": round(history_percent_total, 1),
            "covered_symptoms": list(self.covered_items),
            "volunteered_symptoms": list(self.volunteered),
            "missed_symptoms": list(missed),
            "coverage_percent": coverage_percent,
            "correct_diagnosis": self.extract_diagnosis(),
        }

        return feedback
