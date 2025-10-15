# 🧠 Nueral Watch : Intelligent Data Quality & Drift Monitoring System

### Real-Time Monitoring | Statistical & ML Drift Detection | LLM-Powered Reasoning

---

## 🚀 Overview
**Nueral Watch** is a real-time framework that monitors **data drift**, **model drift**, and **data quality** in machine learning pipelines.  
It integrates **FastAPI**, **LangChain**, **LangGraph**, and **Streamlit** to provide adaptive reasoning, visual insights, and automated decision-making.

---

## 🧩 Features
✅ **Data Drift Detection** — KS Test, PSI, Chi-Square, and advanced ML-based drift checks  
✅ **Model Drift Monitoring** — Detect model performance degradation over time  
✅ **Data Quality Validation** — Missing values, duplicates, outliers, and statistical summary  
✅ **Autonomous Reasoning (LLM)** — LangGraph + LLM decide which tests to run dynamically  
✅ **Streamlit Frontend** — Interactive dashboards with JSON/HTML report export  
✅ **FastAPI Backend** — RESTful APIs for drift detection, data uploads, and reporting  
✅ **Real-Time Insights** — Automated drift summaries in natural language  
✅ **Alerting System** — Trigger notifications on drift detection  
✅ **Versioning** — Track historical drifts, datasets, and test outcomes  

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
├── README.md                      # Project overview, installation, usage, and feature list
├── requirements.txt               # Python dependencies (FastAPI, Pandas, SciPy, LangChain, etc.)
├── .env                           # Environment variables (API keys, DB credentials, etc.)
├── config/
│   ├── settings.py                # Global configurations (thresholds, alert settings)
│   ├── drift_config.json          # Drift detection parameters (KS test, PSI thresholds)
│   ├── remediation_rules.json     # Rules for automated remediation suggestions
│   └── langchain_config.json      # LLM model settings, LangGraph configs
│
├── data/
│   ├── raw/                       # Uploaded raw datasets
│   ├── baseline/                  # Baseline/reference datasets for drift comparison
│   ├── processed/                 # Cleaned/preprocessed datasets
│   └── drift_reports/             # JSON reports of drift & data quality (versioned)
│
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app entrypoint
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── data_upload.py     # Upload endpoints
│   │   │   │   ├── drift_check.py     # Drift detection endpoints
│   │   │   │   ├── quality_check.py   # Data quality endpoints
│   │   │   │   └── remediation.py     # Automated remediation suggestions endpoint
│   │   │   └── dependencies.py        # Shared API dependencies (DB, config, etc.)
│   │   ├── core/
│   │   │   ├── drift/                 # Drift detection algorithms
│   │   │   │   ├── ks_test.py
│   │   │   │   ├── psi.py
│   │   │   │   ├── chi_square.py
│   │   │   │   ├── isolation_forest.py
│   │   │   │   └── jensen_shannon.py
│   │   │   ├── quality/               # Data quality checks
│   │   │   │   ├── missing_values.py
│   │   │   │   ├── outliers.py
│   │   │   │   └── duplicates.py
│   │   │   └── remediation/           # Automated suggestion logic
│   │   │       ├── rules_engine.py
│   │   │       └── code_generator.py
│   │   ├── models/                    # ML models for model drift detection (optional)
│   │   │   └── model_performance.py
│   │   └── utils/
│   │       ├── file_handler.py        # CSV/Parquet upload & read
│   │       ├── versioning.py          # Drift report & baseline versioning
│   │       ├── alerts.py              # Email/Slack notifications
│   │       └── logger.py              # Logging system
│   └── tests/                          # Unit tests for backend
│       ├── test_drift.py
│       ├── test_quality.py
│       └── test_remediation.py
│
├── reasoning/
│   ├── langchain_agent.py             # LangChain agent orchestrating reasoning
│   ├── langgraph_workflow.py          # LangGraph decision workflow
│   ├── summarization/
│   │   ├── llm_summary.py             # LLM-powered natural language summaries
│   │   └── report_formatter.py        # Format JSON + summary
│   └── utils/
│       └── decision_helpers.py        # Helper functions for adaptive reasoning
│
├── frontend/
│   ├── dashboard/
│   │   ├── app.py                     # Frontend entry (Streamlit / Lovable AI / React)
│   │   ├── components/
│   │   │   ├── upload_widget.py       # File upload interface
│   │   │   ├── drift_charts.py        # Drift visualization
│   │   │   ├── quality_charts.py      # Data quality visualization
│   │   │   └── remediation_card.py    # Suggested actions card
│   │   ├── pages/
│   │   │   ├── home.py
│   │   │   ├── drift_report.py
│   │   │   ├── quality_report.py
│   │   │   └── historical_trends.py   # Versioned drift & quality trends
│   │   └── utils/
│   │       ├── api_client.py          # Communicate with backend APIs
│   │       └── plotting_utils.py      # Matplotlib / Plotly / Seaborn helpers
│
├── streaming/                         # Optional real-time monitoring
│   ├── kafka_consumer.py              # Consume incoming data streams
│   ├── drift_monitor.py               # Real-time drift calculation
│   └── alerts_stream.py               # Trigger real-time notifications
│
├── scripts/
│   ├── init_baseline.py               # Initialize reference dataset
│   ├── update_baseline.py             # Update baseline version
│   └── run_drift_pipeline.py          # Run full drift detection workflow
│
└── notebooks/
    ├── EDA.ipynb                      # Exploratory Data Analysis
    ├── demo_drift_check.ipynb         # Demo drift detection
    └── demo_remediation.ipynb         # Demo automated remediation suggestions
