# nlp_preprocess.py
"""
Preprocess health/disease symptom files.

Input (expected in ./data/):
 - dataset.csv                 (disease <-> symptoms mapping; supports either indicator matrix OR symptom columns)
 - symptom_Description.csv
 - symptom_precaution.csv
 - Symptom-severity.csv

Outputs (written to ./data/):
 - cleaned_disease_symptoms.csv   (rows: disease, symptom)
 - symptom_vocab.txt              (one symptom per line)
 - symptom2id.json                (mapping symptom -> integer id)
 - cleaned_symptom_descriptions.csv
 - cleaned_symptom_precautions.csv
 - cleaned_symptom_severity.csv
"""

import pandas as pd
import re, os, json
from pathlib import Path

DATA_DIR = Path("data")
os.makedirs(DATA_DIR, exist_ok=True)

# file paths (adjust if your filenames differ)
FP_DATASET = DATA_DIR / "dataset.csv"
FP_SYM_DESC = DATA_DIR / "symptom_Description.csv"
FP_SYM_PREC = DATA_DIR / "symptom_precaution.csv"
FP_SYM_SEV  = DATA_DIR / "Symptom-severity.csv"

# --- utility functions ---
def clean_text(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s)
    s = s.lower().strip()
    # unify newlines/spaces, remove unwanted characters
    s = re.sub(r"[\r\n]+", " ", s)
    # replace non-alphanumeric with space
    s = re.sub(r"[^a-z0-9\s/,-]", " ", s)
    # collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s

def safe_read_csv(fp: Path):
    if not fp.exists():
        raise FileNotFoundError(f"Missing file: {fp}")
    return pd.read_csv(fp)

# --- load raw files ---
print("Loading files from", DATA_DIR)
dataset = safe_read_csv(FP_DATASET)
sym_desc = safe_read_csv(FP_SYM_DESC)
sym_prec = safe_read_csv(FP_SYM_PREC)
sym_sev  = safe_read_csv(FP_SYM_SEV)

# normalize column names
def norm_cols(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    return df

dataset = norm_cols(dataset)
sym_desc = norm_cols(sym_desc)
sym_prec = norm_cols(sym_prec)
sym_sev  = norm_cols(sym_sev)

# fillna
dataset = dataset.fillna("")
sym_desc = sym_desc.fillna("")
sym_prec = sym_prec.fillna("")
sym_sev  = sym_sev.fillna("")

# --- standardize dataset -> disease,symptom pairs ---
# choose disease column (common names)
possible_disease_cols = [c for c in dataset.columns if any(k in c for k in ("prognosis","disease","diagnosis","disorder"))]
disease_col = possible_disease_cols[0] if possible_disease_cols else dataset.columns[0]
symptom_cols = [c for c in dataset.columns if c != disease_col]

print("Detected disease column:", disease_col)
print("Detected symptom columns (sample):", symptom_cols[:6])

# detect whether symptom columns are indicators (0/1) or actual symptom text
def is_indicator_column(col_series):
    vals = set(str(x).strip().lower() for x in col_series.dropna().unique())
    # common indicator tokens
    allowed = {"0","1","true","false","yes","no", "0.0", "1.0"}
    # if unique values are subset of allowed -> treat as indicator
    return vals.issubset(allowed)

indicator_mode = all(is_indicator_column(dataset[c]) for c in symptom_cols)
print("Indicator-mode detected:", indicator_mode)

disease_sym_pairs = []
if indicator_mode:
    # columns are symptom names, 1/0 indicates presence
    for _, row in dataset.iterrows():
        disease_raw = row[disease_col]
        disease = clean_text(disease_raw)
        for sym_col in symptom_cols:
            val = str(row[sym_col]).strip().lower()
            if val in ("1","true","yes","1.0"):
                sym_name = clean_text(sym_col)   # use column name as symptom
                if sym_name:
                    disease_sym_pairs.append({"disease": disease, "symptom": sym_name})
else:
    # columns contain symptom text in cells (e.g., symptom_1, symptom_2) OR a single "symptoms" column with comma-separated values
    for _, row in dataset.iterrows():
        disease_raw = row[disease_col]
        disease = clean_text(disease_raw)
        for sym_col in symptom_cols:
            cell = str(row[sym_col]).strip()
            if cell == "" or cell.lower() in ("nan",):
                continue
            # split by comma or semicolon if present
            fragments = re.split(r"[;,/]+", cell)
            for frag in fragments:
                frag_clean = clean_text(frag)
                if frag_clean:
                    disease_sym_pairs.append({"disease": disease, "symptom": frag_clean})

ds_df = pd.DataFrame(disease_sym_pairs).drop_duplicates().reset_index(drop=True)
# drop empty symptom rows
ds_df = ds_df[ds_df["symptom"].astype(bool)].reset_index(drop=True)

print(f"Extracted disease-symptom pairs: {len(ds_df)}")
print("Sample pairs:")
print(ds_df.head(8).to_string(index=False))

# --- build symptom vocabulary from dataset + symptom_description + symptom_precaution ---
vocab = set(ds_df["symptom"].unique())

# try to find symptom column in symptom description CSV (common first column)
sym_desc_cols = list(sym_desc.columns)
sym_desc_sym_col = sym_desc_cols[0]
# try to identify description column
desc_col = None
for c in sym_desc_cols[1:]:
    if "desc" in c or "description" in c or "explain" in c or "text" in c:
        desc_col = c
        break
if desc_col is None and len(sym_desc_cols) > 1:
    desc_col = sym_desc_cols[1]

# Clean symptom_description file
sym_desc_clean_rows = []
for _, row in sym_desc.iterrows():
    raw_sym = row.get(sym_desc_sym_col, "")
    raw_desc = row.get(desc_col, "") if desc_col else ""
    s = clean_text(raw_sym)
    d = str(raw_desc).strip()
    sym_desc_clean_rows.append({"symptom": s, "description": d, "description_processed": clean_text(d)})
    if s:
        vocab.add(s)

sym_desc_clean_df = pd.DataFrame(sym_desc_clean_rows).drop_duplicates(subset=["symptom"]).reset_index(drop=True)

# Precautions: combine multiple precaution columns if present
prec_cols = [c for c in sym_prec.columns if c != sym_prec.columns[0]]
prec_sym_col = sym_prec.columns[0]
prec_rows = []
for _, row in sym_prec.iterrows():
    raw_sym = clean_text(row.get(prec_sym_col, ""))
    precs = []
    for c in prec_cols:
        v = str(row.get(c, "")).strip()
        if v and v.lower() not in ("nan", ""):
            precs.append(v)
    prec_text = "; ".join(precs)
    prec_rows.append({"symptom": raw_sym, "precautions": prec_text})
    if raw_sym:
        vocab.add(raw_sym)

sym_prec_clean_df = pd.DataFrame(prec_rows).drop_duplicates(subset=["symptom"]).reset_index(drop=True)

# Severity: find symptom and severity column
sev_cols = list(sym_sev.columns)
sev_sym_col = sev_cols[0]
sev_val_col = None
for c in sev_cols[1:]:
    if any(k in c for k in ("sev","weight","score","value")):
        sev_val_col = c
        break
if sev_val_col is None and len(sev_cols) > 1:
    sev_val_col = sev_cols[1]

sev_rows = []
for _, row in sym_sev.iterrows():
    raw_sym = clean_text(row.get(sev_sym_col, ""))
    raw_val = row.get(sev_val_col, "")
    try:
        val = float(raw_val)
    except Exception:
        # attempt to extract numeric from string
        m = re.search(r"[-+]?\d*\.?\d+", str(raw_val))
        val = float(m.group()) if m else None
    sev_rows.append({"symptom": raw_sym, "severity": val})
    if raw_sym:
        vocab.add(raw_sym)

sym_sev_clean_df = pd.DataFrame(sev_rows).drop_duplicates(subset=["symptom"]).reset_index(drop=True)

# finalize symptom vocab + symptom2id
symptom_vocab = sorted([s for s in vocab if s and isinstance(s, str)])
symptom2id = {s: idx for idx, s in enumerate(symptom_vocab, start=1)}

# Save cleaned outputs
OUT_DS = DATA_DIR / "cleaned_disease_symptoms.csv"
OUT_SYM_VOCAB = DATA_DIR / "symptom_vocab.txt"
OUT_SYM2ID = DATA_DIR / "symptom2id.json"
OUT_SYM_DESC = DATA_DIR / "cleaned_symptom_descriptions.csv"
OUT_SYM_PREC = DATA_DIR / "cleaned_symptom_precautions.csv"
OUT_SYM_SEV = DATA_DIR / "cleaned_symptom_severity.csv"

ds_df.to_csv(OUT_DS, index=False)
with open(OUT_SYM_VOCAB, "w", encoding="utf-8") as f:
    f.write("\n".join(symptom_vocab))
with open(OUT_SYM2ID, "w", encoding="utf-8") as f:
    json.dump(symptom2id, f, indent=2)
sym_desc_clean_df.to_csv(OUT_SYM_DESC, index=False)
sym_prec_clean_df.to_csv(OUT_SYM_PREC, index=False)
sym_sev_clean_df.to_csv(OUT_SYM_SEV, index=False)

# Summary prints
print("\n--- PREPROCESSING SUMMARY ---")
print(f"Unique diseases: {ds_df['disease'].nunique()}")
print(f"Unique symptoms (vocab): {len(symptom_vocab)}")
print("Example symptoms:", symptom_vocab[:20])
print("Saved cleaned files to:", DATA_DIR)

