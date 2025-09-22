import pandas as pd
from collections import defaultdict
from nlp_match import match_symptoms

# Load cleaned dataset
ds_df = pd.read_csv("data/cleaned_disease_symptoms.csv")

# Load severity file
sym_sev = pd.read_csv("data/cleaned_symptom_severity.csv")
severity_dict = dict(zip(sym_sev["symptom"], sym_sev["severity"]))

# Build dictionary: disease → set of symptoms
disease_dict = defaultdict(set)
for _, row in ds_df.iterrows():
    disease_dict[row["disease"]].add(row["symptom"])


def predict_disease(user_input: str, top_k: int = 3):
    """
    Improved disease prediction:
    - Matches symptoms with TF-IDF
    - Requires at least 2 symptoms for prediction
    - Uses coverage ratio (how much of the disease's symptom set is matched)
    """
    # Step 1: Match user symptoms
    matched = [s for s, score in match_symptoms(user_input, top_k=7) if score > 0.4]

    if not matched:
        return [("No clear match", 0)]

    results = []

    # Step 2: Score diseases
    for disease, sym_set in disease_dict.items():
        overlap = set(matched).intersection(sym_set)
        if len(overlap) < 2:
            continue

        coverage = len(overlap) / len(sym_set)  # coverage ratio
        severity_boost = sum(severity_dict.get(sym, 1) for sym in overlap) * 0.1
        score = coverage * 100 + severity_boost

        results.append((disease, score))

    if not results:
        return [("Not enough symptoms for reliable prediction", 0)]

    # Sort by score descending
    results = sorted(results, key=lambda x: x[1], reverse=True)
    return results[:top_k]
