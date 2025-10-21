# 🧠 Nueral Watch : Intelligent Data Quality & Drift Monitoring System

### Real-Time Monitoring | Statistical & ML Drift Detection | LLM-Powered Reasoning

---

## 🚀 Overview
**Nueral Watch** is an end-to-end system that continuously monitors data and model behavior in ML pipelines, detects **distributional drift** and **data-quality issues**, explains them in human language, recommends (and optionally generates) corrective steps, and provides a Streamlit dashboard and REST APIs for developers/analysts..

---

## 🐛 Problem it solves (Why this exists)

✅ ML models degrade when input data distribution changes (data drift) or model-to-production input differs from training (covariate, prior, concept drift).  
✅ Manual monitoring is laborious, error-prone, and slow.  
✅ Teams need actionable, automated, and explainable alerts + reproducible baseline comparisons.  
✅ This project automates detection, reasoning, reporting, and remediation suggestions so models remain reliable in production.

---
## 🧩 Features
✅ **Data Ingestion & File Handling** — 

    What : Upload CSV/Parquet/JSON via Streamlit or accept streams via Kafka.
    Where : frontend/dashboard/components/upload_widget.py, backend/app/utils/file_handler.py, streaming/kafka_consumer.py
    How : 1. Validate schema & dtype on upload.
          2. Save uploaded files under data/raw/ and copy baseline to data/baseline/.
          3. Compute and store metadata (rows, columns, non-null rates) to enable quick comparisons.
          4. Expose /upload_data endpoint for programmatic uploads (backend/app/api/routes/data_upload.py).
    Why important : Reliable ingestion prevents false alarms and ensures reproducibility.
 
✅ **Data Quality Checks** — 

    What : Missing values, duplicates, outliers, datatype mismatches, statistical summaries.
    Where : backend/app/core/quality/{missing_values.py,outliers.py,duplicates.py} and /check_quality API.
    How : 1. Missing values: percent missing per column; flag > thresholds.
          2. Duplicates: row-level duplicate detection with optional key columns.
          3. Outliers (numeric): IQR and Z-score; optional Isolation Forest for multivariate anomalies.
          4. Datatype checks: if declared dtype != observed dtype → flag.
          5. Output: structured JSON with metrics and recommended action(s).
    Frontend : show heatmap of missingness, list columns to fix, sample rows of duplicates.
    
✅ **Statistical Drift Detection (per feature)** — 

    What : Detect distribution changes between baseline and current datasets.
    Where :backend/app/core/drift/{ks_test.py,psi.py,chi_square.py,jensen_shannon.py} and /detect_drift endpoint.
    How (by feature type) : 
            [A] Numerical : 
                1. KS Test (scipy.stats.ks_2samp) — tests sample distribution difference. Output KS statistic + p-value.
                2. PSI (Population Stability Index) — bin distributions, compute PSI; thresholds: <0.1 (no drift), 0.1–0.25 (moderate), >0.25 (large).
            [B] Categorical : 
                1. Chi-square for contingency comparison (scipy.stats.chi2_contingency).
                2. Jensen–Shannon divergence for distribution distance (symmetric and bounded).
    Interpretation: JSON with per-feature scores, severity level, sample size, plots saved to data/drift_reports/.
    
✅ **ML-Based Drift & Anomaly Detection** — 

    What : Use unsupervised models to catch complex shifts not detected by univariate tests.
    Where : backend/app/core/drift/isolation_forest.py and backend/app/models/model_performance.py.
    How : 1. Train IsolationForest on baseline features; score current data; compute fraction flagged.
          2. One-class SVM or autoencoder optional.
          3. For model drift: compare performance metrics (accuracy, F1, RMSE) on labeled recent data vs baseline test set.
    Output: anomaly fraction, drift alert if fraction > threshold.
    
✅ **Model Performance Drift Monitoring** — 

    What : Track model metrics over time (accuracy, ROC-AUC, RMSE) and concept drift (label distribution change).
    Where : backend/app/models/model_performance.py + endpoints to push model predictions + ground truth.
    How : 1. Periodically compute metrics per time window; compare to baseline metrics with control charts and statistical tests (CUSUM, Page-Hinkley).
          2. Trigger "model drift" recommendations when metric drop crosses threshold.
    Use: Decides whether retraining should be recommended or scheduled.

✅ **Versioning & Baselines** — 

    What : Keep historical baselines and drift reports.
    Where : backend/app/utils/versioning.py, data/baseline/, data/drift_reports/.
    How : 1. Each baseline has a version tag + metadata (date, commit hash, training dataset id).
          2. Drift checks store timestamped JSON reports.
          3. UI allows comparing current data against any saved baseline version.
    Benefit: Reproducibility and trending.
    
✅ **LangChain + LangGraph Reasoning & LLM Summaries** — 

    What : Intelligent orchestration: choose tests, summarize findings, generate remediation code/examples.
    Where : reasoning/langchain_agent.py, reasoning/langgraph_workflow.py, reasoning/summarization/llm_summary.py
    How : 1. Decision logic (LangGraph): A rule/graph that takes feature metadata (type, sample size, missingness) and determines which tests to run (KS + PSI vs Chi-Square vs IsolationForest). Stored in config/langchain_config.json.
          2. LLM summarization: Pass selected metrics + human templates to LLM via LangChain to generate human-readable insights and recommended actions. Example output: “Feature income shows large PSI (0.32); suggest retraining model or reweighting samples; consider winsorizing outliers.”
          3. Constraints: LLM used for explanation+templated code generation only — numeric decisions rely on deterministic tests.
    APIs: /get_summary returns text summary + action suggestions
    
---

## 🛠️ Tech Stack
- **Backend**: FastAPI, Python, Pandas, NumPy, SciPy, Scikit-learn  
- **Frontend**: Streamlit  
- **Reasoning Layer**: LangChain, LangGraph  
- **Drift Detection**: KS Test, PSI, Chi-Square, Isolation Forest  
- **Data Visualization**: Plotly, Matplotlib, Streamlit Charts  
- **Version Control**: Git & GitHub  

---

## 🧱 Project Structure

    Nueral Watch/  
    │  
    ├── README.md                                # Project overview, installation, usage, and features    
    ├── requirements.txt                         # Python dependencies (FastAPI, Pandas, SciPy, LangChain, etc.)  
    ├── .env                                     # Environment variables (API keys, DB credentials, etc.)  
    │  
    ├── config/  
    │   ├── settings.py                          # Global configurations (thresholds, alert settings)  
    │   ├── drift_config.json                    # Drift detection parameters (KS test, PSI thresholds)  
    │   ├── remediation_rules.json               # Rules for automated remediation suggestions  
    │   └── langchain_config.json                # LLM model + LangGraph configurations  
    │  
    ├── data/  
    │   ├── raw/                                 # Uploaded raw datasets  
    │   ├── baseline/                            # Reference datasets for drift comparison  
    │   ├── processed/                           # Cleaned / preprocessed datasets  
    │   └── drift_reports/                       # JSON reports of drift & data quality (versioned)  
    │  
    ├── backend/  
    │   ├── app/    
    │   │   ├── main.py                          # FastAPI app entrypoint  
    │   │   │  
    │   │   ├── api/  
    │   │   │   ├── routes/  
    │   │   │   │   ├── data_upload.py           # Upload endpoints  
    │   │   │   │   ├── drift_check.py           # Drift detection endpoints  
    │   │   │   │   ├── quality_check.py         # Data quality endpoints  
    │   │   │   │   └── remediation.py           # Automated remediation endpoints  
    │   │   │   └── dependencies.py              # Shared dependencies (DB, config, etc.)  
    │   │   │  
    │   │   ├── core/  
    │   │   │   ├── drift/  
    │   │   │   │   ├── ks_test.py  
    │   │   │   │   ├── psi.py  
    │   │   │   │   ├── chi_square.py  
    │   │   │   │   ├── isolation_forest.py  
    │   │   │   │   └── jensen_shannon.py  
    │   │   │   │  
    │   │   │   ├── quality/  
    │   │   │   │   ├── missing_values.py  
    │   │   │   │   ├── outliers.py  
    │   │   │   │   └── duplicates.py  
    │   │   │   │  
    │   │   │   └── remediation/  
    │   │   │       ├── rules_engine.py  
    │   │   │       └── code_generator.py  
    │   │   │  
    │   │   ├── models/  
    │   │   │   └── model_performance.py         # For model drift monitoring (optional)  
    │   │   │  
    │   │   └── utils/  
    │   │       ├── file_handler.py              # CSV/Parquet upload & read  
    │   │       ├── versioning.py                # Drift report & baseline versioning  
    │   │       ├── alerts.py                    # Email/Slack notifications  
    │   │       └── logger.py                    # Logging system  
    │   │  
    │   └── tests/  
    │       ├── test_drift.py  
    │       ├── test_quality.py  
    │       └── test_remediation.py    
    │  
    ├── reasoning/  
    │   ├── langchain_agent.py                   # LangChain agent orchestrating reasoning  
    │   ├── langgraph_workflow.py                # LangGraph decision workflow  
    │   │  
    │   ├── summarization/  
    │   │   ├── llm_summary.py                   # LLM-powered natural language summaries  
    │   │   └── report_formatter.py              # Format JSON + summary output  
    │   │  
    │   └── utils/  
    │       └── decision_helpers.py              # Helper functions for adaptive reasoning  
    │  
    ├── frontend/  
    │   ├── dashboard/  
    │   │   ├── app.py                           # Streamlit frontend entry point  
    │   │   │  
    │   │   ├── components/  
    │   │   │   ├── upload_widget.py             # File upload interface  
    │   │   │   ├── drift_charts.py              # Drift visualization  
    │   │   │   ├── quality_charts.py            # Data quality visualization  
    │   │   │   └── remediation_card.py          # Suggested actions display    
    │   │   │  
    │   │   ├── pages/  
    │   │   │   ├── home.py  
    │   │   │   ├── drift_report.py  
    │   │   │   ├── quality_report.py  
    │   │   │   └── historical_trends.py         # Versioned drift & quality trends  
    │   │   │  
    │   │   └── utils/    
    │   │       ├── api_client.py                # Communication with backend APIs  
    │   │       └── plotting_utils.py            # Matplotlib / Plotly helpers  
    │  
    ├── streaming/  
    │   ├── kafka_consumer.py                    # Consume incoming data streams  
    │   ├── drift_monitor.py                     # Real-time drift calculation  
    │   └── alerts_stream.py                     # Trigger real-time notifications  
    │  
    ├── scripts/  
    │   ├── init_baseline.py                     # Initialize reference dataset  
    │   ├── update_baseline.py                   # Update baseline version  
    │   └── run_drift_pipeline.py                # Run full drift detection workflow  
    │  
    └── notebooks/  
    ├── EDA.ipynb                            # Exploratory Data Analysis  
    ├── demo_drift_check.ipynb               # Demo drift detection  
    └── demo_remediation.ipynb               # Demo automated remediation  

