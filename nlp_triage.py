import pandas as pd
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ------------------ Load Datasets ------------------
dataset = pd.read_csv("data/dataset.csv")
sym_prec = pd.read_csv("data/symptom_precaution.csv")
sym_sev = pd.read_csv("data/Symptom-severity.csv")
disease_desc = pd.read_csv("data/symptom_Description.csv")  # ⚠️ file contains disease + description

# Normalize column names
dataset.columns = dataset.columns.str.strip().str.lower()
sym_prec.columns = sym_prec.columns.str.strip().str.lower()
sym_sev.columns = sym_sev.columns.str.strip().str.lower()
disease_desc.columns = disease_desc.columns.str.strip().str.lower()

# Build dictionaries
precaution_dict = dict(zip(sym_prec["symptom"].str.lower(), sym_prec["precautions"]))
severity_dict = dict(zip(sym_sev["symptom"].str.lower(), sym_sev["severity"]))
disease_desc_dict = dict(zip(disease_desc["disease"].str.lower(), disease_desc["description"]))

# Build symptom list
all_symptoms = dataset.drop("disease", axis=1).values.flatten()
all_symptoms = pd.Series(all_symptoms).dropna().str.strip().str.lower().unique().tolist()

# ------------------ Preprocess ------------------
def preprocess(text):
    text = text.lower()
    text = "".join([ch for ch in text if ch not in string.punctuation])
    return text

# ------------------ NLP Matching ------------------
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(all_symptoms)

def match_symptoms(user_input):
    user_input = preprocess(user_input)
    user_vec = vectorizer.transform([user_input])
    similarity = cosine_similarity(user_vec, tfidf_matrix).flatten()

    matched = []
    for idx, score in enumerate(similarity):
        if score > 0.3:  # threshold
            matched.append(all_symptoms[idx])
    return list(set(matched))

# ------------------ Main Triage ------------------
def triage(text):
    if not text:
        return "❗ Please enter a message."

    text_lower = text.lower().strip()
    for disease in disease_desc_dict.keys():
        if disease in text_lower:
            precautions = precaution_dict.get(disease, "No precautions available")
            desc = disease_desc_dict.get(disease, "")
            return (f"📘 <b>{disease.title()}</b><br>{desc}<br><br>"
                f"💡 Suggested Precautions:<br>{precautions}<br><br>"
                "❗ Disclaimer: I’m not a doctor. Please consult a medical professional for diagnosis.")

    
    # ✅ Symptom matching
    matched_symptoms = match_symptoms(text)

    if not matched_symptoms:
        return "❗ I couldn’t recognize any symptoms. Please try again."

    # Predict diseases
    disease_scores = {}
    for _, row in dataset.iterrows():
        disease = row["disease"].lower()
        disease_symptoms = row.dropna().values[1:]
        disease_symptoms = [s.strip().lower() for s in disease_symptoms if isinstance(s, str)]
        score = len(set(matched_symptoms) & set(disease_symptoms)) / (len(disease_symptoms) + 1e-6)
        if score > 0:
            disease_scores[disease] = score * 100

    if not disease_scores:
        return "❗ Not enough symptoms for reliable prediction."

    # Sort by score
    predictions = sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)[:3]

    # Build response
    reply = "<b>🩺 Possible Conditions:</b><br><ol>"
    for disease, score in predictions:
        desc = disease_desc_dict.get(disease, "")
        reply += f"<li><b>{disease.title()}</b> – {score:.0f}% match<br><i>{desc}</i></li>"
    reply += "</ol>"

    # Severity check
    severe_symptoms = [s for s in matched_symptoms if severity_dict.get(s, 0) >= 6]
    if severe_symptoms:
        reply += "<br><b>⚠️ Severe Symptoms Detected:</b><br>" + ", ".join(severe_symptoms)
        reply += "<br>Please consider urgent medical attention.<br>"

    # Precautions
    reply += "<br><b>💡 Suggested Precautions:</b><br>"
    for s in matched_symptoms:
        if s in precaution_dict:
            reply += f"For {s}: {precaution_dict[s]}<br>"

    reply += "<br>❗ Disclaimer: I’m not a doctor. Please consult a medical professional for diagnosis."
    return reply


# ------------------ Debug ------------------
if __name__ == "__main__":
    while True:
        q = input("You: ")
        if q.lower() in ["exit", "quit"]:
            break
        print("Bot:\n", triage(q), "\n")
