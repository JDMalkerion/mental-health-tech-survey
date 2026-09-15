"""
eda.py - Exploratory Data Analysis for OSMI Mental Health in Tech Survey (Day 1).

Executes data loading and prints:
1. Overview: dtypes, null counts per column, cardinality (nunique) per column
2. Missingness summary: % null per column
3. Key frequency distributions (value_counts):
   - Gender
   - Country (top 15)
   - treatment
   - family_history
   - work_interfere
   - no_employees
"""

import sys
import pandas as pd
from data_loader import load_data


def run_eda(csv_path: str = "data/survey.csv") -> None:
    """Runs exploratory data analysis and prints formatted reports to stdout."""
    # 1. Load cleaned data
    df = load_data(csv_path)

    total_rows = len(df)
    total_cols = len(df.columns)

    print("\n" + "#" * 70)
    print("DAY 1 EXPLORATORY DATA ANALYSIS (EDA) REPORT")
    print("#" * 70)
    print(f"Dataset Dimensions: {total_rows:,} rows x {total_cols} columns\n")

    # -------------------------------------------------------------------------
    # SECTION 1: Dtypes, Null Counts, and Cardinality
    # -------------------------------------------------------------------------
    print("=" * 70)
    print("1. COLUMN OVERVIEW: DTYPES, NULL COUNTS & CARDINALITY (nunique)")
    print("=" * 70)

    overview_rows = []
    for idx, col in enumerate(df.columns, 1):
        dtype_str = str(df[col].dtype)
        null_cnt = int(df[col].isna().sum())
        null_pct = (null_cnt / total_rows) * 100
        nunique_cnt = int(df[col].nunique(dropna=True))
        sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "N/A"
        if len(sample_val) > 22:
            sample_val = sample_val[:19] + "..."

        overview_rows.append({
            "#": idx,
            "Column": col,
            "Dtype": dtype_str,
            "Null Count": f"{null_cnt:,}",
            "Null %": f"{null_pct:.1f}%",
            "Cardinality": nunique_cnt,
            "Sample Value": sample_val,
        })

    overview_df = pd.DataFrame(overview_rows)
    # Format table output
    print(overview_df.to_string(index=False))

    # -------------------------------------------------------------------------
    # SECTION 2: Missingness Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("2. MISSINGNESS SUMMARY (% Null per Column)")
    print("=" * 70)

    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Null Count": df.isna().sum().values,
        "Null Percentage": (df.isna().sum().values / total_rows) * 100,
    }).sort_values(by="Null Percentage", ascending=False)

    missing_df["Null Percentage"] = missing_df["Null Percentage"].map(lambda x: f"{x:6.2f}%")
    # Separate columns with nulls vs complete columns
    cols_with_nulls = missing_df[missing_df["Null Count"] > 0]
    complete_cols_count = len(df.columns) - len(cols_with_nulls)

    print("Columns with missing values:")
    print(cols_with_nulls.to_string(index=False))
    print(f"\n({complete_cols_count} columns have 0 missing values: 100% complete)")

    # -------------------------------------------------------------------------
    # SECTION 3: Key Categorical Distributions (value_counts)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("3. CATEGORICAL FREQUENCY DISTRIBUTIONS (value_counts)")
    print("=" * 70)

    target_columns = [
        ("Gender", None),
        ("Country", 15),
        ("treatment", None),
        ("family_history", None),
        ("work_interfere", None),
        ("no_employees", None),
    ]

    for col_name, top_n in target_columns:
        header = f"Distribution: {col_name}" + (f" (Top {top_n})" if top_n else "")
        print(f"\n--- {header} ---")

        # Counts with dropna=False to show missing values if any
        counts = df[col_name].value_counts(dropna=False)
        total_counts = len(df)

        if top_n:
            counts_display = counts.head(top_n)
        else:
            counts_display = counts

        dist_df = pd.DataFrame({
            "Count": counts_display.values,
            "Percentage": (counts_display.values / total_counts) * 100,
        }, index=[repr(k) if pd.isna(k) else str(k) for k in counts_display.index])

        dist_df["Percentage"] = dist_df["Percentage"].map(lambda p: f"{p:6.2f}%")
        dist_df["Count"] = dist_df["Count"].map(lambda c: f"{c:5,d}")
        print(dist_df.to_string())

        if top_n and len(counts) > top_n:
            other_count = counts.iloc[top_n:].sum()
            other_pct = (other_count / total_counts) * 100
            print(f"  [... {len(counts) - top_n} other countries: {other_count:,} respondents ({other_pct:.2f}%)]")

    print("\n" + "#" * 70)
    print("END OF DAY 1 EDA REPORT")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    csv_arg = sys.argv[1] if len(sys.argv) > 1 else "data/survey.csv"
    run_eda(csv_arg)
