# Mental Health in Tech Survey: Policy Benchmarking Analysis

An exploratory data analysis and interactive Streamlit dashboard benchmarking mental health treatment rates, workplace attitudes, and disclosure dynamics across the technology sector using the 2014 OSMI Mental Health in Tech Survey.

**Live Demo:** https://mental-health-tech-survey-gujdvph8mrjmyygqexj8pd.streamlit.app/
---

## Business Context & Framing

For technology employers and People Operations teams, mental health support is often a major blind spot. While companies invest heavily in Employee Assistance Programs (EAPs) and wellness benefits, leadership rarely has empirical benchmarks to evaluate whether their utilization rates, disclosure cultures, and stigma levels reflect industry norms or indicate organizational underperformance.

This project frames the 2014 Open Sourcing Mental Illness (OSMI) survey as a policy benchmarking tool. By evaluating treatment-seeking behaviors, institutional benefits awareness, and disclosure comfort across company headcount tiers, sovereign jurisdictions, and distributed work arrangements, an employer can quantitatively determine where internal support policies under- or over-perform relative to industry peers.

---

## Key Insights

Based on verified analyses of the cleaned 1,251-respondent cohort:

- **Mental vs. Physical Stigma Gap (~5x Disparity)**: Employees report nearly fivefold higher fear of negative career consequences when discussing mental health compared to physical health (**23.02% vs. 4.64%**). Stigma peaks acutely during recruitment: **80.18%** of tech candidates refuse to disclose a mental health issue during job interviews (vs. **39.65%** for physical conditions).
- **Family History as the Strongest Clean Predictor**: Having a family history of mental illness more than doubles the likelihood of seeking treatment (**74.03% vs. 35.43%**, Odds Ratio: **2.65**). *(Note: While `work_interfere` correlates strongly with treatment at $r = 0.55$, it is excluded from independent predictor framing because the question is conditioned on already having a self-identified mental health condition, making it circular rather than an independent causal driver.)*
- **Awareness Trumps Provision**: Providing benefits raises treatment rates to **63.85%** (vs. **48.25%** where benefits are absent). However, when employees do not know whether benefits exist ("Don't know"), treatment plummets to **37.10%**—worse than non-provision. Knowing specific care options elevates treatment to **69.02%** (+27.7 percentage points over unawareness).
- **Geographic Divergence in Care-Seeking**: Significant geographic variation exists across qualifying nations ($\ge15$ respondents), ranging from **61.90%** in Australia, **54.69%** in the United States, **51.39%** in Canada, and **50.00%** in the United Kingdom down to **46.67%** in Germany and **33.33%** in the Netherlands. Within the US, state-level rates diverge from **70.37%** (Ohio) and **67.86%** (Illinois) to **40.00%** (Tennessee).
- **Remote Workers Show Higher Disclosure Willingness**: Distributed work does not foster disclosure isolation. Remote employees ($\ge50\%$ remote) report slightly higher willingness to discuss mental health with their supervisor (**43.86% vs. 39.65%**) and coworkers (**22.11% vs. 15.89%**) than in-office peers.
- **No Strong Signal / Neutral Findings**:
  - *Company Size*: Headcount bands show minimal impact on treatment rates, ranging narrowly from **43.94%** (6–25 employees) to **55.70%** (1–5 employees), with enterprise organizations (>1,000 employees) settling at **51.96%**. Large corporate scale does not inherently improve treatment access.
  - *Age Distribution*: Age shows virtually zero linear correlation with treatment seeking ($r = +0.06$); both treated and untreated cohorts share an identical median age of **31.0 years**.

---

## Project Structure

- **`data_loader.py`**: Data ingestion and cleaning pipeline. Filters invalid age values to `[18, 75]`, normalizes free-text gender strings via explicit canonical mapping to `Male` (78.02%), `Female` (19.58%), and `Other` (2.40%), standardizes country names, converts non-US state entries to null, and preserves structural nulls in `work_interfere`, `self_employed`, and `comments`.
- **`analysis.py`**: Statistical engine computing geographic breakdowns (countries and US states with $\ge15$ respondents), bivariate crosstabs, an interpretable logistic regression model, mental vs. physical stigma ratios, and remote work disclosure splits.
- **`eda.py`**: Command-line exploratory analysis script outputting column-by-column missingness, cardinality, and frequency distributions.
- **`eda_notebook.ipynb`**: Self-contained, deployment-ready Jupyter notebook containing the full 20-chart EDA across Univariate, Bivariate, and Multivariate tiers, followed by a clinical pair plot and detailed policy recommendations.
- **`app.py`**: Interactive Streamlit dashboard featuring global sidebar filters, executive KPI cards, and 4 Plotly charts with a unified dark-mode theme (`#12141A`) and semantic color palette.

---

## Tech Stack

- Python 3.14
- Pandas & NumPy
- Plotly & Matplotlib / Seaborn
- Streamlit
- Scikit-learn

---

## How to Run Locally

Follow these steps to set up and run the project locally:

```bash
git clone <repo-url>
cd mental-health-tech-survey
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dataset Setup

The raw survey dataset is gitignored. Download the dataset directly from Kaggle:

1. Download the [OSMI Mental Health in Tech Survey (2014)](https://www.kaggle.com/datasets/osmi/mental-health-in-tech-survey).
2. Place the downloaded `survey.csv` inside the `data/` directory at the project root:
   ```bash
   mkdir -p data
   mv /path/to/downloaded/survey.csv data/survey.csv
   ```

### Launch Interactive Dashboard

Once dependencies are installed and `data/survey.csv` is in place, launch the Streamlit dashboard:

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

### View Full EDA Notebook

To inspect the 20-chart exploratory analysis notebook top-to-bottom:

```bash
jupyter notebook eda_notebook.ipynb
```

