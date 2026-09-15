"""
analysis.py - Analytical engine for the OSMI Mental Health in Tech Survey (Day 2).

Provides specialized analysis functions:
1. geographic_treatment_rates: Country & US State treatment rates (>= 15 respondents)
2. geographic_attitudes: Workplace mental health attitudes across qualifying countries
3. treatment_predictors: Crosstabs and logistic regression feature importance
4. mental_vs_physical_gap: Quantifying disparity between mental vs physical health stigma
5. remote_work_disclosure: Willingness to discuss mental health by remote work status
"""

from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from data_loader import load_data


def geographic_treatment_rates(
    df: pd.DataFrame, min_respondents: int = 15
) -> Dict[str, pd.DataFrame]:
    """
    Computes treatment rates (% Yes) by Country and US State,
    filtering to locations with at least `min_respondents` respondents.
    """
    # 1. Country breakdown
    country_counts = df["Country"].value_counts()
    qualifying_countries = country_counts[country_counts >= min_respondents].index

    country_df = df[df["Country"].isin(qualifying_countries)]
    country_rates = (
        country_df.groupby("Country")
        .apply(
            lambda g: pd.Series(
                {
                    "Respondents": len(g),
                    "Treatment_Yes": (g["treatment"] == "Yes").sum(),
                    "Treatment_Rate_%": (g["treatment"] == "Yes").mean() * 100,
                }
            ),
            include_groups=False,
        )
        .sort_values(by="Treatment_Rate_%", ascending=False)
    )
    country_rates["Respondents"] = country_rates["Respondents"].astype(int)
    country_rates["Treatment_Yes"] = country_rates["Treatment_Yes"].astype(int)

    # 2. US State breakdown
    us_df = df[df["Country"] == "United States"]
    state_counts = us_df["state"].dropna().value_counts()
    qualifying_states = state_counts[state_counts >= min_respondents].index

    state_df = us_df[us_df["state"].isin(qualifying_states)]
    state_rates = (
        state_df.groupby("state")
        .apply(
            lambda g: pd.Series(
                {
                    "Respondents": len(g),
                    "Treatment_Yes": (g["treatment"] == "Yes").sum(),
                    "Treatment_Rate_%": (g["treatment"] == "Yes").mean() * 100,
                }
            ),
            include_groups=False,
        )
        .sort_values(by="Treatment_Rate_%", ascending=False)
    )
    state_rates["Respondents"] = state_rates["Respondents"].astype(int)
    state_rates["Treatment_Yes"] = state_rates["Treatment_Yes"].astype(int)

    return {"country": country_rates, "state": state_rates}


def geographic_attitudes(
    df: pd.DataFrame, min_respondents: int = 15
) -> pd.DataFrame:
    """
    Computes attitude and benefits rates by Country for countries with >= min_respondents.
    Includes treatment rate, benefits provision, care options awareness, and consequence perception.
    """
    country_counts = df["Country"].value_counts()
    qualifying_countries = country_counts[country_counts >= min_respondents].index
    c_df = df[df["Country"].isin(qualifying_countries)]

    attitudes = (
        c_df.groupby("Country")
        .apply(
            lambda g: pd.Series(
                {
                    "Respondents": len(g),
                    "Treatment_Rate_%": (g["treatment"] == "Yes").mean() * 100,
                    "Benefits_Yes_%": (g["benefits"] == "Yes").mean() * 100,
                    "Benefits_DontKnow_%": (g["benefits"] == "Don't know").mean() * 100,
                    "Care_Options_Yes_%": (g["care_options"] == "Yes").mean() * 100,
                    "Consequence_Yes_%": (g["mental_health_consequence"] == "Yes").mean() * 100,
                    "Consequence_Maybe_%": (g["mental_health_consequence"] == "Maybe").mean() * 100,
                    "Consequence_No_%": (g["mental_health_consequence"] == "No").mean() * 100,
                }
            ),
            include_groups=False,
        )
        .sort_values(by="Treatment_Rate_%", ascending=False)
    )
    attitudes["Respondents"] = attitudes["Respondents"].astype(int)
    return attitudes


def treatment_predictors(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes bivariate crosstabs of treatment vs key predictors and fits
    an interpretable logistic regression model on the entire cleaned dataset.
    """
    predictor_cols = [
        "family_history",
        "work_interfere",
        "benefits",
        "care_options",
        "no_employees",
    ]

    crosstabs = {}
    for col in predictor_cols:
        series_clean = df[col].fillna("Missing")
        ct = pd.crosstab(series_clean, df["treatment"], normalize="index") * 100
        ct["Total_Respondents"] = series_clean.value_counts()
        ct["Treatment_Rate_%"] = ct["Yes"] if "Yes" in ct.columns else 0.0
        crosstabs[col] = ct.sort_values(by="Treatment_Rate_%", ascending=False)

    # Logistic Regression: encode features
    features = [
        "family_history",
        "work_interfere",
        "benefits",
        "care_options",
        "no_employees",
        "remote_work",
    ]
    X_raw = df[features].copy()
    X_raw["work_interfere"] = X_raw["work_interfere"].fillna("Missing")
    X = pd.get_dummies(X_raw, drop_first=True, dtype=int)
    y = (df["treatment"] == "Yes").astype(int)

    # Fit simple interpretable logistic regression without penalty for exploratory analysis
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)

    coef_df = pd.DataFrame(
        {
            "Feature": X.columns,
            "Coefficient": model.coef_[0],
            "Odds_Ratio": np.exp(model.coef_[0]),
            "Abs_Coefficient": np.abs(model.coef_[0]),
        }
    ).sort_values(by="Abs_Coefficient", ascending=False)

    return {
        "crosstabs": crosstabs,
        "model": model,
        "coefficients": coef_df.reset_index(drop=True),
        "feature_names": list(X.columns),
    }


def mental_vs_physical_gap(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Quantifies the stigma disparity between mental health and physical health
    across consequences, interview disclosure, and comparative perception.
    """
    # 1. Consequence comparison
    m_consequence = df["mental_health_consequence"].value_counts(normalize=True) * 100
    p_consequence = df["phys_health_consequence"].value_counts(normalize=True) * 100
    consequence_gap = pd.DataFrame(
        {
            "Mental_Consequence_%": m_consequence,
            "Physical_Consequence_%": p_consequence,
        }
    ).reindex(["No", "Maybe", "Yes"])
    consequence_gap["Disparity_Ratio (Mental/Phys)"] = (
        consequence_gap["Mental_Consequence_%"] / consequence_gap["Physical_Consequence_%"]
    )

    # 2. Interview disclosure comparison
    m_interview = df["mental_health_interview"].value_counts(normalize=True) * 100
    p_interview = df["phys_health_interview"].value_counts(normalize=True) * 100
    interview_gap = pd.DataFrame(
        {
            "Mental_Interview_%": m_interview,
            "Physical_Interview_%": p_interview,
        }
    ).reindex(["No", "Maybe", "Yes"])
    interview_gap["Disparity_Ratio (Phys/Mental)"] = (
        interview_gap["Physical_Interview_%"] / interview_gap["Mental_Interview_%"]
    )

    # 3. Overall perception of parity
    stated_gap = (
        df["mental_vs_physical"]
        .value_counts(dropna=False, normalize=True)
        .mul(100)
        .to_frame(name="Response_%")
    )

    return {
        "consequence_gap": consequence_gap,
        "interview_gap": interview_gap,
        "stated_gap": stated_gap,
    }


def remote_work_disclosure(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Analyzes willingness to discuss mental health with supervisor and coworkers,
    split by remote work status (Yes vs No).
    """
    sup_ct = pd.crosstab(df["remote_work"], df["supervisor"], normalize="index") * 100
    cow_ct = pd.crosstab(df["remote_work"], df["coworkers"], normalize="index") * 100

    col_order = ["Yes", "Some of them", "No"]
    sup_ct = sup_ct[[c for c in col_order if c in sup_ct.columns]]
    cow_ct = cow_ct[[c for c in col_order if c in cow_ct.columns]]

    return {"supervisor": sup_ct, "coworkers": cow_ct}


def run_full_analysis() -> None:
    """Executes all analysis functions and prints formatted reports to stdout."""
    df = load_data()

    print("\n" + "#" * 74)
    print("DAY 2 ANALYTICAL REPORT: OSMI MENTAL HEALTH IN TECH SURVEY")
    print("#" * 74)

    # -------------------------------------------------------------------------
    # 1. Geographic Treatment Rates
    # -------------------------------------------------------------------------
    print("\n" + "=" * 74)
    print("1. GEOGRAPHIC TREATMENT RATES (Countries & US States with >= 15 respondents)")
    print("=" * 74)
    geo_rates = geographic_treatment_rates(df, min_respondents=15)

    print("\n--- Country Treatment Rates (15+ Respondents) ---")
    c_df = geo_rates["country"].copy()
    c_df["Treatment_Rate_%"] = c_df["Treatment_Rate_%"].map(lambda x: f"{x:6.2f}%")
    print(c_df.to_string())

    print("\n--- US State Treatment Rates (15+ Respondents) ---")
    s_df = geo_rates["state"].copy()
    s_df["Treatment_Rate_%"] = s_df["Treatment_Rate_%"].map(lambda x: f"{x:6.2f}%")
    print(s_df.to_string())

    # -------------------------------------------------------------------------
    # 2. Geographic Attitudes
    # -------------------------------------------------------------------------
    print("\n" + "=" * 74)
    print("2. GEOGRAPHIC ATTITUDES & BENEFITS BREAKDOWN (Top Countries)")
    print("=" * 74)
    attitudes = geographic_attitudes(df, min_respondents=15)
    formatted_att = attitudes.copy()
    for col in formatted_att.columns:
        if "%" in col:
            formatted_att[col] = formatted_att[col].map(lambda x: f"{x:5.1f}%")
    print(formatted_att.to_string())

    # -------------------------------------------------------------------------
    # 3. Treatment Predictors & Logistic Regression
    # -------------------------------------------------------------------------
    print("\n" + "=" * 74)
    print("3. TREATMENT PREDICTORS & LOGISTIC REGRESSION MODEL")
    print("=" * 74)
    predictors = treatment_predictors(df)

    print("\n--- Bivariate Crosstabs (% Treatment within Category) ---")
    for feature_name, ct in predictors["crosstabs"].items():
        print(f"\nFeature: [{feature_name}]")
        display_ct = ct.copy()
        if "No" in display_ct.columns:
            display_ct["No_%"] = display_ct["No"].map(lambda x: f"{x:5.1f}%")
        if "Yes" in display_ct.columns:
            display_ct["Yes_%"] = display_ct["Yes"].map(lambda x: f"{x:5.1f}%")
        cols_to_show = [c for c in ["Total_Respondents", "Yes_%", "No_%"] if c in display_ct.columns]
        print(display_ct[cols_to_show].to_string())

    print("\n--- Logistic Regression Coefficients (Sorted by |Effect Size|) ---")
    coef_df = predictors["coefficients"].copy()
    coef_df["Coefficient"] = coef_df["Coefficient"].map(lambda x: f"{x:+7.4f}")
    coef_df["Odds_Ratio"] = coef_df["Odds_Ratio"].map(lambda x: f"{x:7.3f}")
    print(coef_df[["Feature", "Coefficient", "Odds_Ratio"]].to_string(index=False))

    # -------------------------------------------------------------------------
    # 4. Mental vs. Physical Gap
    # -------------------------------------------------------------------------
    print("\n" + "=" * 74)
    print("4. MENTAL VS. PHYSICAL HEALTH STIGMA GAP")
    print("=" * 74)
    gap = mental_vs_physical_gap(df)

    print("\n--- Consequence Discussion Risk (Mental vs Physical) ---")
    con_df = gap["consequence_gap"].copy()
    con_df["Mental_Consequence_%"] = con_df["Mental_Consequence_%"].map(lambda x: f"{x:6.2f}%")
    con_df["Physical_Consequence_%"] = con_df["Physical_Consequence_%"].map(lambda x: f"{x:6.2f}%")
    con_df["Disparity_Ratio (Mental/Phys)"] = con_df["Disparity_Ratio (Mental/Phys)"].map(lambda x: f"{x:5.2f}x")
    print(con_df.to_string())

    print("\n--- Interview Disclosure Willingness (Mental vs Physical) ---")
    int_df = gap["interview_gap"].copy()
    int_df["Mental_Interview_%"] = int_df["Mental_Interview_%"].map(lambda x: f"{x:6.2f}%")
    int_df["Physical_Interview_%"] = int_df["Physical_Interview_%"].map(lambda x: f"{x:6.2f}%")
    int_df["Disparity_Ratio (Phys/Mental)"] = int_df["Disparity_Ratio (Phys/Mental)"].map(lambda x: f"{x:5.2f}x")
    print(int_df.to_string())

    print("\n--- Perception: 'Does your employer view mental & physical health equally?' ---")
    st_df = gap["stated_gap"].copy()
    st_df["Response_%"] = st_df["Response_%"].map(lambda x: f"{x:6.2f}%")
    print(st_df.to_string())

    # -------------------------------------------------------------------------
    # 5. Remote Work Disclosure
    # -------------------------------------------------------------------------
    print("\n" + "=" * 74)
    print("5. REMOTE WORK DISCLOSURE WILLINGNESS (Remote vs Non-Remote)")
    print("=" * 74)
    remote_res = remote_work_disclosure(df)

    print("\n--- Willingness to Discuss with Supervisor (%) ---")
    sup_disp = remote_res["supervisor"].copy()
    for col in sup_disp.columns:
        sup_disp[col] = sup_disp[col].map(lambda x: f"{x:5.1f}%")
    print(sup_disp.to_string())

    print("\n--- Willingness to Discuss with Coworkers (%) ---")
    cow_disp = remote_res["coworkers"].copy()
    for col in cow_disp.columns:
        cow_disp[col] = cow_disp[col].map(lambda x: f"{x:5.1f}%")
    print(cow_disp.to_string())

    print("\n" + "#" * 74)
    print("END OF DAY 2 ANALYTICAL REPORT")
    print("#" * 74 + "\n")


if __name__ == "__main__":
    run_full_analysis()
