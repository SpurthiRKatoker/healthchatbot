import pandas as pd

# Load all extracted files
dataset = pd.read_csv("data/dataset.csv")
sym_desc = pd.read_csv("data/symptom_Description.csv")
sym_prec = pd.read_csv("data/symptom_precaution.csv")
sym_sev = pd.read_csv("data/Symptom-severity.csv")


# Check the first few rows of each
print("Dataset:")
print(dataset.head(), "\n")

print("Symptom Description:")
print(sym_desc.head(), "\n")

print("Symptom Precaution:")
print(sym_prec.head(), "\n")

print("Symptom Severity:")
print(sym_sev.head(), "\n")
