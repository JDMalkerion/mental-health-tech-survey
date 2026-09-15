"""
data_loader.py - Data ingestion and cleaning pipeline for the OSMI Mental Health in Tech Survey.

Day 1 deliverables:
- Read raw CSV
- Clean Age: retain respondents aged 18 to 75, log dropped count
- Normalize Gender: map free-text responses to Male, Female, Other
- Standardize Country & State: strip whitespace, keep state only for United States
- Preserve untouched nulls in work_interfere, self_employed, and comments
"""

from pathlib import Path
from typing import Union
import logging
import numpy as np
import pandas as pd

# Configure module logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Explicit mapping dictionary for free-text Gender normalization
# Free-text variants canonicalized to 'Male' and 'Female'; everything else becomes 'Other'
GENDER_MAP = {
    # Male variants
    "male": "Male",
    "m": "Male",
    "man": "Male",
    "cis male": "Male",
    "cis man": "Male",
    "male (cis)": "Male",
    # Female variants
    "female": "Female",
    "f": "Female",
    "woman": "Female",
    "cis female": "Female",
    "female (cis)": "Female",
    "cis-female/femme": "Female",
}


def load_data(path: Union[str, Path] = "data/survey.csv") -> pd.DataFrame:
    """
    Loads, cleans, and standardizes the Mental Health in Tech Survey dataset.

    Parameters:
        path (str or Path): Filepath to the raw survey CSV. Defaults to 'data/survey.csv'.

    Returns:
        pd.DataFrame: Cleaned DataFrame ready for exploratory data analysis.
    """
    file_path = Path(path)
    if not file_path.exists():
        # Fallback to path relative to this script's directory
        alt_path = Path(__file__).resolve().parent / path
        if alt_path.exists():
            file_path = alt_path
        else:
            raise FileNotFoundError(f"Survey data file not found at '{path}' or '{alt_path}'")

    print(f"\n{'='*70}")
    print(f"LOADING DATA: {file_path}")
    print(f"{'='*70}")

    df = pd.read_csv(file_path)
    initial_rows = len(df)
    print(f"Initial row count: {initial_rows:,} rows across {len(df.columns)} columns")

    # -------------------------------------------------------------------------
    # 1. Clean Age: filter out rows outside [18, 75]
    # -------------------------------------------------------------------------
    age_valid_mask = (df["Age"] >= 18) & (df["Age"] <= 75)
    dropped_age_rows = (~age_valid_mask).sum()
    dropped_ages = df.loc[~age_valid_mask, "Age"].tolist()

    df = df[age_valid_mask].copy()
    print(f"\n[Age Cleaning]")
    print(f"  - Dropped {dropped_age_rows} row(s) outside [18, 75] years old: {dropped_ages}")
    print(f"  - Rows retained: {len(df):,} / {initial_rows:,} ({len(df)/initial_rows:.1%})")
    print(f"  - Cleaned Age range: min={df['Age'].min()}, max={df['Age'].max()}, median={df['Age'].median()}")

    # -------------------------------------------------------------------------
    # 2. Normalize Gender: explicit mapping dict (male/m/cis male/man -> Male,
    #    female/f/cis female/woman -> Female, everything else -> Other)
    # -------------------------------------------------------------------------
    print(f"\n[Gender Normalization]")
    print("--- Gender Value Counts BEFORE Normalization (Raw Top 15 + summary) ---")
    raw_gender_counts = df["Gender"].value_counts(dropna=False)
    print(raw_gender_counts.head(15))
    print(f"Total distinct raw gender responses: {df['Gender'].nunique()}")

    # Standardize string format: strip whitespace & lowercase for matching
    cleaned_gender_key = df["Gender"].fillna("").astype(str).str.strip().str.lower()
    df["Gender"] = cleaned_gender_key.map(GENDER_MAP).fillna("Other")

    print("\n--- Gender Value Counts AFTER Normalization ---")
    norm_gender_counts = df["Gender"].value_counts(dropna=False)
    print(norm_gender_counts)
    print(f"Bucketing percentages:")
    for gender, count in norm_gender_counts.items():
        print(f"  - {gender:6s}: {count:5,d} ({count/len(df):6.2%})")

    # -------------------------------------------------------------------------
    # 3. Standardize Country & State:
    #    - Strip whitespace, consistent casing
    #    - Keep state only where Country == 'United States', else set to null
    # -------------------------------------------------------------------------
    print(f"\n[Country & State Standardization]")
    df["Country"] = df["Country"].astype(str).str.strip()

    # Nullify state for any record where Country is not 'United States'
    non_us_with_state = ((df["Country"] != "United States") & df["state"].notna()).sum()
    df.loc[df["Country"] != "United States", "state"] = np.nan

    # Clean state for United States rows: strip whitespace
    us_mask = df["Country"] == "United States"
    df.loc[us_mask, "state"] = df.loc[us_mask, "state"].astype(str).str.strip()
    # If state was string 'nan' or empty, convert back to np.nan
    df.loc[us_mask & df["state"].isin(["nan", "", "None"]), "state"] = np.nan

    print(f"  - Standardized Country strings across {df['Country'].nunique()} unique countries")
    print(f"  - Set state to null for {non_us_with_state} non-US respondent(s) who had state values")
    print(f"  - US respondents with state: {df.loc[us_mask, 'state'].notna().sum():,} / {us_mask.sum():,}")
    print(f"  - Non-US respondents with state: {(df.loc[~us_mask, 'state'].notna()).sum()} (strictly 0)")

    # -------------------------------------------------------------------------
    # 4. Null Preservation:
    #    Leaves work_interfere, self_employed, comments nulls untouched.
    # -------------------------------------------------------------------------
    print(f"\n[Null Preservation Check]")
    print(f"  - self_employed null count : {df['self_employed'].isna().sum():4d} (untouched)")
    print(f"  - work_interfere null count: {df['work_interfere'].isna().sum():4d} (untouched)")
    print(f"  - comments null count      : {df['comments'].isna().sum():4d} (untouched)")

    print(f"\n{'='*70}")
    print(f"CLEANING COMPLETE: {len(df):,} records ready")
    print(f"{'='*70}\n")

    return df


if __name__ == "__main__":
    df_clean = load_data()
