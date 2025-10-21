"""
Home Page for Neural Watch Dashboard
Phase 1: Data Ingestion & Quality Setup
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from frontend.dashboard.utils.api_client import get_api_client
from frontend.dashboard.components.upload_widget import (
    render_upload_widget, render_recent_uploads, render_baseline_info
)


def render_home_page():
    """Render the home page"""
    
    # Header
    st.title("🧠 Neural Watch")
    st.markdown("### Intelligent Data Quality & Drift Monitoring System 3.0")
    st.markdown("---")
    
    # Check backend health
    api_client = get_api_client()
    success, health_data = api_client.health_check()
    
    if success:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.success("✅ Backend: Connected")
        with col2:
            st.info(f"📦 Version: {health_data.get('version', 'N/A')}")
        with col3:
            st.info(f"🔧 Phase: {health_data.get('phase', 'N/A').split('-')[0]}")
    else:
        st.error("❌ Backend: Disconnected")
        st.error(f"Error: {health_data.get('detail', 'Cannot connect to backend')}")
        st.stop()
    
    st.markdown("---")
    
    # Main content - two columns
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Upload widget
        render_upload_widget()
    
    with col_right:
        # Baseline info
        render_baseline_info()
        
        st.markdown("---")
        
        # Recent uploads
        render_recent_uploads()
    
    # Footer
    st.markdown("---")
    st.markdown("### 📚 Quick Guide")
    
    with st.expander("How to use Neural Watch (Phase 1)"):
        st.markdown("""
        **Step 1: Upload Your First Dataset**
        - Click "Choose a file" and select your CSV, JSON, or Parquet file
        - Preview the data to ensure it loaded correctly
        - Check "Set as Baseline" to create a reference dataset
        - Click "Upload"
        
        **Step 2: Understanding the Results**
        - **Upload Summary**: See basic statistics about your dataset
        - **Missing Values**: Identify columns with missing data
        - **Validation Report**: Check for any data quality issues
        - **Baseline Comparison**: Compare with previous uploads
        
        **Step 3: Upload Additional Datasets**
        - Upload new datasets without checking "Set as Baseline"
        - Neural Watch will automatically compare them to your baseline
        - Review differences in schema, row counts, and data types
        
        **Coming in Phase 2:**
        - 🔍 Comprehensive data quality checks
        - 📊 Visual quality reports and heatmaps
        - 🎯 Automated issue detection
        """)
    
    with st.expander("Features in This Phase"):
        st.markdown("""
        **✅ Implemented:**
        - File upload (CSV, JSON, Parquet)
        - File format and size validation
        - Schema validation against baseline
        - Metadata extraction (rows, columns, dtypes)
        - Missing value detection
        - Duplicate row detection
        - Baseline versioning
        - Automated baseline comparison
        
        **🚧 Coming Soon (Phase 2):**
        - Advanced quality checks (outliers, datatype mismatches)
        - Visual quality reports with heatmaps
        - Detailed column statistics
        
        **🚧 Coming Later:**
        - Phase 3: Statistical drift detection (KS Test, PSI, Chi-Square)
        - Phase 4: LLM-powered insights and remediation suggestions
        - Phase 5: Model performance monitoring and alerts
        """)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Neural Watch - Home",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_home_page()