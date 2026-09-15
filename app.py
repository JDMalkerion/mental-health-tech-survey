"""
app.py - Interactive Streamlit dashboard for OSMI Mental Health in Tech Survey (Day 2).

Layout and features:
- Sidebar filters: Country (multiselect, top 10 default), Gender, Company Size, Remote Work
- KPI row: Total respondents, Overall treatment rate, Family history %, Remote workers %
- 4 Interactive Plotly charts:
  1. Treatment rate by country (>=15 baseline respondents)
  2. Treatment predictor crosstab as grouped bar chart
  3. Mental vs physical health consequence comparison
  4. Remote work vs disclosure willingness (supervisor / coworkers)
"""

from typing import List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_loader

# -----------------------------------------------------------------------------
# Color palette & shared Plotly layout template
# -----------------------------------------------------------------------------
COLOR_TEAL = "#4FA8A0"       # primary / mental health / treatment
COLOR_AMBER = "#E0A85C"      # secondary comparison / physical health
COLOR_CORAL = "#D97D72"      # reserved — stigma/concern highlights only
COLOR_SLATE = "#5B6478"      # neutral / baseline "No" bars
COLOR_TEXT_MUTED = "#8B90A0"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#12141A",
    plot_bgcolor="#12141A",
    font=dict(color="#EDEAE3", family="sans-serif"),
    xaxis=dict(gridcolor="#262A35", zerolinecolor="#262A35"),
    yaxis=dict(gridcolor="#262A35", zerolinecolor="#262A35"),
)


def apply_theme(fig, xaxis_extra=None, yaxis_extra=None, **kwargs):
    """
    Applies the shared dark theme layout to a Plotly Figure, safely merging
    custom axis parameters without keyword argument collisions.
    """
    layout = dict(PLOTLY_LAYOUT)
    if xaxis_extra:
        layout["xaxis"] = {**layout["xaxis"], **xaxis_extra}
    if yaxis_extra:
        layout["yaxis"] = {**layout["yaxis"], **yaxis_extra}
    fig.update_layout(**layout, **kwargs)
    return fig

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Mental Health in Tech Dashboard",
    page_icon="🧠",
)

# Custom styling — dark-mode card surfaces and muted caption text
st.markdown(
    """
    <style>
    /* Metric card: dark surface consistent with secondaryBackgroundColor */
    [data-testid="stMetric"] {
        background-color: #1B1E27;
        border: 1px solid #262A35;
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 6px rgba(0, 0, 0, 0.35);
    }
    /* Muted label text inside KPI cards */
    [data-testid="stMetricLabel"] p {
        color: #8B90A0 !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    /* Metric value — slightly brighter */
    [data-testid="stMetricValue"] {
        color: #EDEAE3 !important;
    }
    .main-title {
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #8B90A0;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. Header & Overview
# -----------------------------------------------------------------------------
st.title("🧠 Mental Health in Tech Survey Dashboard")
st.markdown(
    "<p class='sub-title'>Exploring mental health treatment rates, workplace attitudes, "
    "stigma disparities, and disclosure willingness across the tech industry (OSMI 2014).</p>",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 3. Cached Data Ingestion
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading cleaned survey dataset...")
def get_cached_data() -> pd.DataFrame:
    """Loads cleaned OSMI survey dataset using Day 1 data_loader pipeline."""
    return data_loader.load_data()


raw_df = get_cached_data()

# Identify countries with >= 15 respondents in the unfiltered baseline dataset
baseline_country_counts = raw_df["Country"].value_counts()
baseline_15plus_countries: List[str] = baseline_country_counts[
    baseline_country_counts >= 15
].index.tolist()

# Top 10 countries by respondent count for default filter selection
top_10_countries = baseline_country_counts.head(10).index.tolist()

# -----------------------------------------------------------------------------
# 4. Dynamic Sidebar Filters
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Filter Survey Data")

# 1. Country Filter (multiselect with top 10 as default)
all_countries = sorted(raw_df["Country"].unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Country",
    options=all_countries,
    default=top_10_countries,
    help="Filter by respondent countries (defaults to top 10 countries by sample size).",
)

# 2. Gender Filter
gender_options = ["All"] + sorted(raw_df["Gender"].unique().tolist())
selected_gender = st.sidebar.selectbox(
    "Gender",
    options=gender_options,
    index=0,
    help="Filter by normalized gender category (Male, Female, Other).",
)

# 3. Company Size Filter
# Standard logical order for company sizes
size_order = ["1-5", "6-25", "26-100", "100-500", "500-1000", "More than 1000"]
existing_sizes = [s for s in size_order if s in raw_df["no_employees"].unique()]
selected_size = st.sidebar.selectbox(
    "Company Size (Employees)",
    options=["All"] + existing_sizes,
    index=0,
    help="Filter by employer headcount.",
)

# 4. Remote Work Filter
selected_remote = st.sidebar.selectbox(
    "Remote Work",
    options=["All", "Yes", "No"],
    index=0,
    help="Filter by whether respondents work remotely at least 50% of the time.",
)

# -----------------------------------------------------------------------------
# 5. Apply Filtering
# -----------------------------------------------------------------------------
filtered_df = raw_df.copy()

if selected_countries:
    filtered_df = filtered_df[filtered_df["Country"].isin(selected_countries)]
else:
    # If user deselects all countries, keep empty dataset
    filtered_df = filtered_df.iloc[0:0]

if selected_gender != "All":
    filtered_df = filtered_df[filtered_df["Gender"] == selected_gender]

if selected_size != "All":
    filtered_df = filtered_df[filtered_df["no_employees"] == selected_size]

if selected_remote != "All":
    filtered_df = filtered_df[filtered_df["remote_work"] == selected_remote]

# -----------------------------------------------------------------------------
# 6. KPI Row & Empty State Handling
# -----------------------------------------------------------------------------
total_filtered = len(filtered_df)

if total_filtered == 0:
    st.warning("⚠️ No survey responses match the active filter criteria. Please broaden your selections.")
else:
    treatment_yes_cnt = (filtered_df["treatment"] == "Yes").sum()
    treatment_rate = (treatment_yes_cnt / total_filtered) * 100

    family_hist_cnt = (filtered_df["family_history"] == "Yes").sum()
    family_hist_rate = (family_hist_cnt / total_filtered) * 100

    remote_cnt = (filtered_df["remote_work"] == "Yes").sum()
    remote_rate = (remote_cnt / total_filtered) * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total Respondents",
            value=f"{total_filtered:,}",
            help="Total survey respondents matching the active sidebar filters.",
        )
    with col2:
        st.metric(
            label="Treatment Rate",
            value=f"{treatment_rate:.1f}%",
            help="Percentage of respondents who have sought treatment for a mental health condition.",
        )
    with col3:
        st.metric(
            label="Family History",
            value=f"{family_hist_rate:.1f}%",
            help="Percentage of respondents with a family history of mental illness.",
        )
    with col4:
        st.metric(
            label="Remote Workers",
            value=f"{remote_rate:.1f}%",
            help="Percentage of respondents working remotely at least 50% of the time.",
        )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 7. Row 1 Visualizations: Geography & Treatment Predictors
    # -------------------------------------------------------------------------
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("🌍 Treatment Rate by Country")
        st.caption("Restricted to countries with ≥15 respondents in the baseline dataset.")

        # Filter active data to baseline 15+ countries
        geo_subset = filtered_df[filtered_df["Country"].isin(baseline_15plus_countries)]

        if len(geo_subset) == 0:
            st.info("No respondents in the qualifying 15+ baseline countries under active filters.")
        else:
            geo_rates = (
                geo_subset.groupby("Country")
                .apply(
                    lambda g: pd.Series(
                        {
                            "Respondents": len(g),
                            "Treatment_Rate_%": (g["treatment"] == "Yes").mean() * 100,
                        }
                    ),
                    include_groups=False,
                )
                .reset_index()
                .sort_values(by="Treatment_Rate_%", ascending=True)
            )

            fig_geo = px.bar(
                geo_rates,
                x="Treatment_Rate_%",
                y="Country",
                orientation="h",
                text="Treatment_Rate_%",
                hover_data={"Respondents": True, "Treatment_Rate_%": ":.1f%"},
                labels={"Treatment_Rate_%": "Treatment Rate (%)", "Country": "Country"},
            )
            fig_geo.update_traces(
                marker_color=COLOR_TEAL,
                texttemplate="%{text:.1f}%",
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="#12141A", size=12),
            )
            apply_theme(
                fig_geo,
                xaxis_extra=dict(range=[0, 100], title="Treatment Rate (%)"),
                yaxis_extra=dict(title=""),
                margin=dict(l=20, r=20, t=30, b=20),
                height=380,
            )
            st.plotly_chart(fig_geo, use_container_width=True)

    with row1_col2:
        st.subheader("🔬 Treatment Rate by Key Predictors")
        predictor_labels = {
            "family_history": "Family History of Mental Illness",
            "work_interfere": "Work Interference Level",
            "care_options": "Care Options Awareness",
            "benefits": "Mental Health Benefits Provided",
            "no_employees": "Company Size (Employees)",
        }

        selected_feature = st.selectbox(
            "Select Predictor Variable to Cross-Tabulate:",
            options=list(predictor_labels.keys()),
            format_func=lambda k: predictor_labels[k],
            index=0,
            help="Compare % Yes treatment across sub-categories of this factor.",
        )

        pred_data = filtered_df.copy()
        pred_data[selected_feature] = pred_data[selected_feature].fillna("Missing")

        # Compute crosstab rate
        ct_df = (
            pred_data.groupby(selected_feature)
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
            .reset_index()
        )

        # Logical ordering for specific categorical features
        if selected_feature == "work_interfere":
            order_map = {"Often": 1, "Sometimes": 2, "Rarely": 3, "Never": 4, "Missing": 5}
            ct_df["sort_key"] = ct_df[selected_feature].map(order_map).fillna(99)
            ct_df = ct_df.sort_values("sort_key")
        elif selected_feature == "no_employees":
            order_map = {s: i for i, s in enumerate(size_order)}
            ct_df["sort_key"] = ct_df[selected_feature].map(order_map).fillna(99)
            ct_df = ct_df.sort_values("sort_key")
        else:
            ct_df = ct_df.sort_values(by="Treatment_Rate_%", ascending=False)

        # Assign semantic colors: high-rate bars → teal, low-rate → slate
        pred_median = ct_df["Treatment_Rate_%"].median()
        bar_colors = [
            COLOR_TEAL if rate >= pred_median else COLOR_SLATE
            for rate in ct_df["Treatment_Rate_%"]
        ]

        fig_pred = go.Figure(
            go.Bar(
                x=ct_df[selected_feature],
                y=ct_df["Treatment_Rate_%"],
                marker_color=bar_colors,
                text=[f"{v:.1f}%" for v in ct_df["Treatment_Rate_%"]],
                textposition="outside",
                textfont=dict(color="#EDEAE3"),
                customdata=ct_df["Respondents"],
                hovertemplate=(
                    f"<b>%{{x}}</b><br>"
                    "Treatment Rate: %{y:.1f}%<br>"
                    "Respondents: %{customdata}<extra></extra>"
                ),
            )
        )
        apply_theme(
            fig_pred,
            xaxis_extra=dict(title=predictor_labels[selected_feature]),
            yaxis_extra=dict(title="Treatment Rate (%)", range=[0, 105]),
            margin=dict(l=20, r=20, t=30, b=20),
            height=380,
        )
        st.plotly_chart(fig_pred, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 8. Row 2 Visualizations: Stigma Gap & Remote Work Disclosure
    # -------------------------------------------------------------------------
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("⚖️ Mental vs. Physical Health Gap")
        st.caption("Side-by-side comparison of consequence fears and interview willingness.")

        gap_metric = st.radio(
            "Comparison Metric:",
            options=["Workplace Consequence Fear", "Job Interview Disclosure Willingness"],
            horizontal=True,
            help="Switch between fear of negative workplace consequences and willingness to bring up conditions in an interview.",
        )

        categories = ["No", "Maybe", "Yes"]
        if gap_metric == "Workplace Consequence Fear":
            m_pcts = [
                (filtered_df["mental_health_consequence"] == cat).mean() * 100 for cat in categories
            ]
            p_pcts = [
                (filtered_df["phys_health_consequence"] == cat).mean() * 100 for cat in categories
            ]
            chart_title = "Anticipated Negative Workplace Consequence"
        else:
            m_pcts = [
                (filtered_df["mental_health_interview"] == cat).mean() * 100 for cat in categories
            ]
            p_pcts = [
                (filtered_df["phys_health_interview"] == cat).mean() * 100 for cat in categories
            ]
            chart_title = "Willingness to Discuss in Job Interview"

        fig_gap = go.Figure()
        fig_gap.add_trace(
            go.Bar(
                x=categories,
                y=m_pcts,
                name="Mental Health",
                marker_color=COLOR_TEAL,
                text=[f"{v:.1f}%" for v in m_pcts],
                textposition="outside",
                textfont=dict(color="#EDEAE3"),
            )
        )
        fig_gap.add_trace(
            go.Bar(
                x=categories,
                y=p_pcts,
                name="Physical Health",
                marker_color=COLOR_AMBER,
                text=[f"{v:.1f}%" for v in p_pcts],
                textposition="outside",
                textfont=dict(color="#EDEAE3"),
            )
        )
        apply_theme(
            fig_gap,
            barmode="group",
            margin=dict(l=20, r=20, t=30, b=20),
            height=380,
            xaxis_extra=dict(title="Response Category"),
            yaxis_extra=dict(title="Response Rate (%)", range=[0, 100]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_gap, use_container_width=True)

    with row2_col2:
        st.subheader("💻 Remote Work vs. Disclosure Willingness")
        st.caption("Willingness to discuss mental health with supervisors vs coworkers.")

        # Compute breakdown by remote work
        rem_groups = ["No (In-Office)", "Yes (Remote)"]
        sup_yes_rates = []
        cow_yes_rates = []

        for r_val in ["No", "Yes"]:
            subset = filtered_df[filtered_df["remote_work"] == r_val]
            if len(subset) > 0:
                sup_yes_rates.append((subset["supervisor"] == "Yes").mean() * 100)
                cow_yes_rates.append((subset["coworkers"] == "Yes").mean() * 100)
            else:
                sup_yes_rates.append(0.0)
                cow_yes_rates.append(0.0)

        fig_rem = go.Figure()
        fig_rem.add_trace(
            go.Bar(
                x=rem_groups,
                y=sup_yes_rates,
                name="Discuss with Supervisor",
                marker_color=COLOR_TEAL,
                text=[f"{v:.1f}%" for v in sup_yes_rates],
                textposition="outside",
                textfont=dict(color="#EDEAE3"),
            )
        )
        fig_rem.add_trace(
            go.Bar(
                x=rem_groups,
                y=cow_yes_rates,
                name="Discuss with Coworkers",
                marker_color=COLOR_AMBER,
                text=[f"{v:.1f}%" for v in cow_yes_rates],
                textposition="outside",
                textfont=dict(color="#EDEAE3"),
            )
        )
        apply_theme(
            fig_rem,
            barmode="group",
            margin=dict(l=20, r=20, t=30, b=20),
            height=380,
            xaxis_extra=dict(title="Work Setting"),
            yaxis_extra=dict(title="Disclosure Willingness (% Yes)", range=[0, 65]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_rem, use_container_width=True)
