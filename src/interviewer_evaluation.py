def evaluate_question(question: str, patient: dict, explicitly_covered=None, volunteered=None, patient_answer=""):
    """
    Evaluate doctor question against patient symptoms.

    Tracks:
    - explicitly_covered: symptoms matched by direct questions
    - volunteered: symptoms actually reported for "any other symptoms"
    """
    if explicitly_covered is None:
        explicitly_covered = []
    if volunteered is None:
        volunteered = []

    true_symptoms = [s.lower() for s in patient.get("symptoms", [])]
    answer_lower = patient_answer.lower()

    # Check for explicitly asked symptoms
    if "any other symptoms" not in question.lower():
        for symptom in true_symptoms:
            if symptom in question.lower() and symptom not in explicitly_covered:
                explicitly_covered.append(symptom)
    else:
        # Only count volunteered symptoms actually reported
        prefix = "yes, i am experiencing "
        if answer_lower.startswith(prefix):
            # Correctly extract reported symptoms
            reported_text = patient_answer[len(prefix):]  # slice after prefix
            reported = [s.strip().lower().rstrip('.') for s in reported_text.split(",")]
            for s in reported:
                if s not in explicitly_covered and s not in volunteered:
                    volunteered.append(s)
        # If patient said "No other symptoms", do nothing

    coverage = len(explicitly_covered) / len(true_symptoms) if true_symptoms else 0

    text = (f"Coverage: {int(coverage*100)}% | "
            f"explicitly covered: {explicitly_covered} | "
            f"volunteered: {volunteered}")

    return text, explicitly_covered, volunteered
