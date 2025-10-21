"""
Upload Widget Component for Neural Watch
Phase 1: Data Ingestion & Quality Setup
Streamlit component for file uploads
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from frontend.dashboard.utils.api_client import get_api_client


def render_upload_widget():
    """
    Render the file upload widget in Streamlit
    
    Returns:
        Tuple of (uploaded_file, upload_response) or (None, None)
    """
    st.subheader("📤 Upload Dataset")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file (CSV, JSON, or Parquet)",
        type=['csv', 'json', 'parquet'],
        help="Upload your dataset for quality checks and drift monitoring"
    )
    
    if uploaded_file is not None:
        # Display file info
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Filename", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        with col3:
            st.metric("File Type", uploaded_file.type)
        
        # Preview data
        with st.expander("👁️ Preview Data (first 10 rows)", expanded=False):
            try:
                # Read file based on type
                if uploaded_file.name.endswith('.csv'):
                    df_preview = pd.read_csv(uploaded_file)
                    uploaded_file.seek(0)  # Reset file pointer
                elif uploaded_file.name.endswith('.json'):
                    df_preview = pd.read_json(uploaded_file)
                    uploaded_file.seek(0)
                elif uploaded_file.name.endswith('.parquet'):
                    df_preview = pd.read_parquet(uploaded_file)
                    uploaded_file.seek(0)
                else:
                    df_preview = None
                
                if df_preview is not None:
                    st.dataframe(df_preview.head(10), use_container_width=True)
                    
                    # Basic stats
                    st.markdown("**Quick Stats:**")
                    stats_col1, stats_col2, stats_col3 = st.columns(3)
                    with stats_col1:
                        st.metric("Rows", len(df_preview))
                    with stats_col2:
                        st.metric("Columns", len(df_preview.columns))
                    with stats_col3:
                        missing_pct = (df_preview.isnull().sum().sum() / 
                                     (len(df_preview) * len(df_preview.columns)) * 100)
                        st.metric("Missing %", f"{missing_pct:.1f}%")
                    
            except Exception as e:
                st.error(f"Error reading file preview: {str(e)}")
        
        # Upload options
        st.markdown("---")
        st.markdown("**Upload Options:**")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            is_baseline = st.checkbox(
                "Set as Baseline",
                value=False,
                help="Set this dataset as the baseline/reference for future drift comparisons"
            )
            
            description = st.text_input(
                "Description (optional)",
                placeholder="e.g., Production data from Q1 2025",
                help="Add a description to identify this dataset later"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            upload_button = st.button(
                "🚀 Upload",
                type="primary",
                use_container_width=True
            )
        
        # Handle upload
        if upload_button:
            with st.spinner("Uploading and validating file..."):
                api_client = get_api_client()
                
                # Upload file
                success, response = api_client.upload_file_from_streamlit(
                    uploaded_file,
                    is_baseline=is_baseline,
                    description=description if description else None
                )
                
                if success:
                    st.success("✅ File uploaded successfully!")
                    
                    # Display upload details
                    st.markdown("---")
                    st.markdown("### 📊 Upload Summary")
                    
                    # Metadata
                    metadata = response.get('metadata', {})
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Rows", metadata.get('rows', 'N/A'))
                    with col2:
                        st.metric("Columns", metadata.get('columns', 'N/A'))
                    with col3:
                        st.metric("File Size", f"{metadata.get('file_size_mb', 0):.2f} MB")
                    with col4:
                        duplicates = metadata.get('duplicates', {})
                        st.metric("Duplicates", f"{duplicates.get('percentage', 0):.1f}%")
                    
                    # Missing values
                    if 'missing_values' in metadata:
                        missing = metadata['missing_values']
                        cols_with_missing = missing.get('columns_with_missing', [])
                        
                        if cols_with_missing:
                            st.warning(f"⚠️ {len(cols_with_missing)} column(s) have missing values")
                            with st.expander("View columns with missing values"):
                                missing_df = pd.DataFrame([
                                    {
                                        'Column': col,
                                        'Missing Count': missing['counts'].get(col, 0),
                                        'Missing %': f"{missing['percentages'].get(col, 0):.2f}%"
                                    }
                                    for col in cols_with_missing
                                ])
                                st.dataframe(missing_df, use_container_width=True)
                    
                    # Validation report
                    if 'validation_report' in response and response['validation_report']:
                        validation = response['validation_report']
                        
                        if validation.get('warnings'):
                            st.warning("⚠️ Validation Warnings:")
                            for warning in validation['warnings']:
                                st.markdown(f"- {warning}")
                        
                        if validation.get('checks_passed'):
                            with st.expander("✅ Validation Checks Passed"):
                                for check in validation['checks_passed']:
                                    st.markdown(f"- {check}")
                    
                    # Baseline info
                    if 'baseline_info' in response and response['baseline_info']:
                        baseline = response['baseline_info']
                        st.info(f"🎯 Baseline created: **{baseline['version_id']}**")
                    
                    # Comparison with baseline
                    if 'comparison_with_baseline' in response and response['comparison_with_baseline']:
                        comparison = response['comparison_with_baseline']
                        
                        if comparison.get('has_baseline'):
                            st.markdown("### 🔍 Comparison with Baseline")
                            st.info(f"Compared with: **{comparison['baseline_version']}**")
                            
                            differences = comparison.get('differences', [])
                            if differences:
                                st.warning(f"⚠️ {len(differences)} difference(s) detected")
                                
                                with st.expander("View differences"):
                                    for diff in differences:
                                        field = diff.get('field', 'Unknown')
                                        st.markdown(f"**{field.replace('_', ' ').title()}:**")
                                        
                                        if field == 'rows':
                                            st.markdown(f"- Baseline: {diff['baseline']:,}")
                                            st.markdown(f"- Current: {diff['current']:,}")
                                            st.markdown(f"- Change: {diff['change']:+,} ({diff.get('change_percentage', 0):+.2f}%)")
                                        elif field == 'columns':
                                            st.markdown(f"- Baseline: {diff['baseline']}")
                                            st.markdown(f"- Current: {diff['current']}")
                                            st.markdown(f"- Change: {diff['change']:+}")
                                        elif field == 'column_schema':
                                            if diff.get('missing_columns'):
                                                st.markdown(f"- Missing: {', '.join(diff['missing_columns'])}")
                                            if diff.get('extra_columns'):
                                                st.markdown(f"- Extra: {', '.join(diff['extra_columns'])}")
                                        elif field == 'data_types':
                                            for change in diff.get('changes', []):
                                                st.markdown(f"- {change['column']}: {change['baseline_dtype']} → {change['current_dtype']}")
                                        
                                        st.markdown("---")
                            else:
                                st.success("✅ No significant differences from baseline")
                    
                    return uploaded_file, response
                    
                else:
                    error_detail = response.get('detail', 'Unknown error')
                    st.error(f"❌ Upload failed: {error_detail}")
                    return None, None
        
        return uploaded_file, None
    
    return None, None


def render_recent_uploads():
    """Render a list of recent uploads"""
    st.subheader("📁 Recent Uploads")
    
    api_client = get_api_client()
    success, response = api_client.list_uploads()
    
    if success:
        files = response.get('files', [])
        
        if files:
            # Show only last 5 uploads
            recent_files = files[:5]
            
            for file_info in recent_files:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{file_info['filename']}**")
                    
                    with col2:
                        st.markdown(f"📊 {file_info['file_size_mb']} MB")
                    
                    with col3:
                        # View button
                        if st.button("View", key=f"view_{file_info['file_id']}"):
                            st.session_state['selected_file_id'] = file_info['file_id']
                    
                    st.markdown(f"*Uploaded: {file_info['upload_timestamp']}*")
                    st.markdown("---")
            
            # View all link
            if len(files) > 5:
                st.info(f"Showing 5 of {len(files)} uploads. View all in the uploads page.")
        else:
            st.info("No uploads yet. Upload your first dataset above!")
    else:
        st.error("Error loading recent uploads")


def render_baseline_info():
    """Render current baseline information"""
    st.subheader("🎯 Current Baseline")
    
    api_client = get_api_client()
    success, response = api_client.list_baselines()
    
    if success:
        baselines = response.get('baselines', [])
        
        if baselines:
            latest_baseline = baselines[0]  # Already sorted by creation date
            
            st.info(f"**Version:** {latest_baseline['version_id']}")
            st.markdown(f"**Description:** {latest_baseline.get('description', 'N/A')}")
            st.markdown(f"**Created:** {latest_baseline['created_at']}")
            
            metadata = latest_baseline.get('source_metadata', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", metadata.get('rows', 'N/A'))
            with col2:
                st.metric("Columns", metadata.get('columns', 'N/A'))
            with col3:
                st.metric("Size", f"{metadata.get('file_size_mb', 0):.2f} MB")
            
            # View all baselines
            if len(baselines) > 1:
                with st.expander(f"📋 View all {len(baselines)} baseline(s)"):
                    for baseline in baselines:
                        st.markdown(f"- **{baseline['version_id']}** ({baseline['created_at']})")
        else:
            st.warning("No baseline set yet. Upload a dataset and mark it as baseline.")
    else:
        st.error("Error loading baseline information")