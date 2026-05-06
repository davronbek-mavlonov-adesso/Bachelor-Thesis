"""
ETL pipeline for AI Impact on IT Consulting Survey
Transforms long-format CSV into a wide per-respondent DataFrame
"""

import glob
import os
import pandas as pd
import numpy as np
import re


def _find_csv() -> str:
    """Return the most recently modified survey CSV in the script's directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = glob.glob(os.path.join(script_dir, "*.csv"))
    if not candidates:
        raise FileNotFoundError("No CSV file found in the survey directory.")
    # Pick the newest file by modification time
    latest = max(candidates, key=os.path.getmtime)
    print(f"[ETL] Using data file: {os.path.basename(latest)}")
    return latest


CSV_PATH = _find_csv()

# ── Likert ordering ───────────────────────────────────────────────────────────
LIKERT_ORDER = [
    "strongly disagree",
    "disagree",
    "somewhat disagree",
    "somewhat agree",
    "agree",
    "strongly agree",
]

FREQUENCY_ORDER = [
    "Less than once a month",
    "A few times a month",
    "A few times a week",
    "Daily",
    "Several times a day",
]

EXPERIENCE_ORDER = [
    "Less than 1 year",
    "1-2 years",
    "3-5 years",
    "6-10 years",
    "More than 10 years",
]


def run_etl(csv_path: str = CSV_PATH) -> dict:
    """
    Returns a dict with:
        wide       – one row per respondent, Q1-Q4 as filter cols + Q5-Q19
        raw        – cleaned raw long-format dataframe
        questions  – mapping {number: question_text}
        q4_options – all distinct multi-select options for Q4
    """
    # ── Extract ───────────────────────────────────────────────────────────────
    raw = pd.read_csv(csv_path, sep=";", quotechar='"', dtype=str)
    raw.columns = ["Number", "Question", "Email", "Answer", "Position", "Option"]
    raw["Number"] = raw["Number"].str.strip().astype(int)
    raw["Answer"] = raw["Answer"].str.strip()
    raw["Email"] = raw["Email"].str.strip().str.lower()

    # Assign anonymous ID to blank emails
    anonymous_mask = raw["Email"].isna() | (raw["Email"] == "")
    raw.loc[anonymous_mask, "Email"] = "anonymous"

    # Build question map
    questions = (
        raw.drop_duplicates("Number")
        .set_index("Number")["Question"]
        .str.strip()
        .to_dict()
    )

    # ── Transform ─────────────────────────────────────────────────────────────

    # Get all respondents (from Q1 which every respondent answered)
    respondents = raw[raw["Number"] == 1]["Email"].unique().tolist()

    wide_rows = []
    for email in respondents:
        resp_data = raw[raw["Email"] == email]
        row: dict = {"email": email}

        for qnum in range(1, 20):
            q_rows = resp_data[resp_data["Number"] == qnum]

            if qnum == 4:
                # Multi-select: store as pipe-separated string
                vals = q_rows["Answer"].dropna().tolist()
                row[f"q{qnum}"] = " | ".join(sorted(set(vals))) if vals else np.nan
            else:
                vals = q_rows["Answer"].dropna().tolist()
                row[f"q{qnum}"] = vals[0] if vals else np.nan

        wide_rows.append(row)

    wide = pd.DataFrame(wide_rows)

    # Normalise Likert columns to lowercase for consistent ordering
    likert_cols = [f"q{n}" for n in [5, 12, 13, 14, 15, 16, 17]]
    for col in likert_cols:
        if col in wide.columns:
            wide[col] = wide[col].str.lower().str.strip()

    # Categorical ordering
    wide["q1"] = pd.Categorical(wide["q1"], ordered=False)
    wide["q2"] = pd.Categorical(wide["q2"], categories=FREQUENCY_ORDER, ordered=True)
    wide["q3"] = pd.Categorical(wide["q3"], categories=EXPERIENCE_ORDER, ordered=True)
    for col in likert_cols:
        wide[col] = pd.Categorical(wide[col], categories=LIKERT_ORDER, ordered=True)

    # Derive domain from email
    wide["domain"] = wide["email"].apply(
        lambda x: re.search(r"@(.+)$", str(x)).group(1) if "@" in str(x) else "external"
    )

    # Q4 distinct options
    q4_options = sorted(
        {
            opt.strip()
            for cell in wide["q4"].dropna()
            for opt in str(cell).split("|")
            if opt.strip()
        }
    )

    return {
        "wide": wide,
        "raw": raw,
        "questions": questions,
        "q4_options": q4_options,
    }


if __name__ == "__main__":
    data = run_etl()
    print(f"Respondents: {len(data['wide'])}")
    print(f"Columns: {list(data['wide'].columns)}")
    print(data["wide"].head(3).to_string())
