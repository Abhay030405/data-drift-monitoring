"""
Neural Watch Streamlit Dashboard - Main Application
Phase 2: Data Ingestion & Quality Checks
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from frontend.dashboard.pages.home import render_home_page
from frontend.dashboard.pages.quality_report import render_quality_report_page


def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title="Neural Watch",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    h1 {
        color: #1f77b4;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=Neural+Watch", use_container_width=True)
        st.markdown("---")
        
        # Navigation
        st.markdown("## 📍 Navigation")
        page = st.radio(
            "Go to:",
            ["🏠 Home", "📊 Quality Reports", "📈 Drift Reports", "📜 History"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Phase indicator
        st.markdown("### 🔧 Current Phase")
        st.info("**Phase 2**: Data Quality Checks")
        
        st.markdown("---")
        
        # System info
        st.markdown("### ℹ️ System Info")
        st.markdown("**Version:** 3.0")
        st.markdown("**Environment:** Development")
        
        st.markdown("---")
        
        # Quick links
        st.markdown("### 🔗 Quick Links")
        st.markdown("- [API Docs](http://localhost:8000/docs)")
        st.markdown("- [GitHub](https://github.com)")
        st.markdown("- [Documentation](https://docs.neuralwatch.io)")
    
    # Main content based on navigation
    if page == "🏠 Home":
        render_home_page()
    
    elif page == "📊 Quality Reports":
        render_quality_report_page()
    
    elif page == "📈 Drift Reports":
        st.title("📈 Drift Detection Reports")
        st.info("🚧 Coming in Phase 3: Statistical drift detection and visualization")
        st.markdown("""
        **Features coming soon:**
        - KS Test results per feature
        - PSI (Population Stability Index) analysis
        - Chi-Square tests for categorical features
        - Distribution comparison plots
        - Drift severity indicators
        """)
    
    elif page == "📜 History":
        st.title("📜 Historical Trends")
        st.info("🚧 Coming in Phase 3+: Time-series analysis of drift and quality metrics")
        st.markdown("""
        **Features coming soon:**
        - Historical drift trends
        - Quality score evolution
        - Model performance over time
        - Baseline version comparison
        """)


if __name__ == "__main__":
    main()