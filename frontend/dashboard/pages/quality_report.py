"""
Quality Report Page for Neural Watch
Phase 2: Data Quality Checks
"""
import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import json

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from frontend.dashboard.utils.api_client import get_api_client
from frontend.dashboard.components.quality_charts import (
    render_quality_score_gauge, render_missing_values_chart,
    render_outliers_boxplot, render_duplicate_pie_chart,
    render_score_breakdown, render_data_type_distribution
)
from frontend.dashboard.components.issue_cards import (
    render_all_issues, render_summary_stats, render_detailed_stats
)


def render_quality_report_page():
    """Render the quality report page"""
    
    st.title("📊 Data Quality Report")
    st.markdown("### Comprehensive quality analysis of your datasets")
    st.markdown("---")
    
    api_client = get_api_client()
    
    # Step 1: Select data source
    st.subheader("1️⃣ Select Data Source")
    
    col1, col2 = st.columns(2)
    
    with col1:
        data_source = st.radio(
            "Choose data source:",
            ["Previously Uploaded File", "Upload New File"],
            horizontal=True
        )
    
    file_id = None
    uploaded_file = None
    
    if data_source == "Previously Uploaded File":
        # Get list of uploads
        success, response = api_client.list_uploads()
        
        if success and response.get('files'):
            files = response['files']
            file_options = {f"{f['filename']} ({f['upload_timestamp']})": f['file_id'] 
                          for f in files}
            
            selected_file = st.selectbox(
                "Select file:",
                options=list(file_options.keys())
            )
            
            if selected_file:
                file_id = file_options[selected_file]
        else:
            st.warning("No uploaded files found. Please upload a file first.")
            return
    
    else:
        uploaded_file = st.file_uploader(
            "Upload file for quality check:",
            type=['csv', 'json', 'parquet']
        )
    
    # Step 2: Configure quality checks
    st.markdown("---")
    st.subheader("2️⃣ Configure Quality Checks")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        check_missing = st.checkbox("Missing Values", value=True)
    
    with col2:
        check_duplicates = st.checkbox("Duplicates", value=True)
    
    with col3:
        check_outliers = st.checkbox("Outliers", value=True)
    
    with col4:
        outlier_method = st.selectbox(
            "Outlier Method:",
            options=['iqr', 'z_score', 'both'],
            index=0
        )
    
    # Step 3: Run quality check
    st.markdown("---")
    
    if st.button("🚀 Run Quality Check", type="primary", use_container_width=True):
        if not file_id and not uploaded_file:
            st.error("Please select or upload a file first!")
            return
        
        with st.spinner("Running quality checks... This may take a moment."):
            # Run quality check
            if file_id:
                success, response = api_client.check_quality(
                    file_id=file_id,
                    check_missing=check_missing,
                    check_duplicates=check_duplicates,
                    check_outliers=check_outliers,
                    outlier_method=outlier_method
                )
            else:
                success, response = api_client.check_quality_from_streamlit(
                    uploaded_file=uploaded_file,
                    check_missing=check_missing,
                    check_duplicates=check_duplicates,
                    check_outliers=check_outliers,
                    outlier_method=outlier_method
                )
            
            if success:
                st.success("✅ Quality check completed!")
                
                # Store report in session state
                st.session_state['current_quality_report'] = response.get('report')
            else:
                st.error(f"❌ Quality check failed: {response.get('detail', 'Unknown error')}")
                return
    
    # Step 4: Display results
    if 'current_quality_report' in st.session_state:
        st.markdown("---")
        st.subheader("📈 Quality Report Results")
        
        report = st.session_state['current_quality_report']
        
        # Overall Quality Score
        st.markdown("### 🎯 Overall Quality Score")
        score_result = report.get('quality_score', {})
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            render_quality_score_gauge(
                score_result.get('overall_score', 0),
                score_result.get('grade', 'Unknown')
            )
        
        with col2:
            render_score_breakdown(score_result)
        
        st.markdown("---")
        
        # Summary Statistics
        st.markdown("### 📊 Summary Statistics")
        render_summary_stats(report)
        
        st.markdown("---")
        
        # Issues and Recommendations
        st.markdown("### ⚠️ Issues & Recommendations")
        recommendations = report.get('recommendations', [])
        render_all_issues(recommendations)
        
        st.markdown("---")
        
        # Detailed Visualizations
        st.markdown("### 📈 Detailed Analysis")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Missing Values", "Duplicates", "Outliers", "Data Types"
        ])
        
        with tab1:
            st.markdown("#### Missing Values Analysis")
            missing_analysis = report.get('missing_values', {})
            
            if missing_analysis.get('overall_missing_percentage', 0) > 0:
                render_missing_values_chart(missing_analysis)
                
                # Missing patterns
                patterns = report.get('missing_patterns', {})
                if patterns:
                    st.markdown("**Missing Value Patterns:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Rows with Missing",
                            f"{patterns.get('rows_with_missing_percentage', 0)}%"
                        )
                    
                    with col2:
                        st.metric(
                            "Rows with Multiple Missing",
                            patterns.get('rows_with_multiple_missing', 0)
                        )
                    
                    with col3:
                        st.metric(
                            "Completely Empty Rows",
                            patterns.get('completely_empty_rows', 0)
                        )
            else:
                st.success("✅ No missing values detected!")
        
        with tab2:
            st.markdown("#### Duplicate Analysis")
            duplicate_analysis = report.get('duplicates', {})
            
            if duplicate_analysis.get('total_duplicates', 0) > 0:
                render_duplicate_pie_chart(duplicate_analysis)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Total Duplicates",
                        duplicate_analysis.get('total_duplicates', 0)
                    )
                
                with col2:
                    st.metric(
                        "Duplicate Groups",
                        duplicate_analysis.get('duplicate_groups', 0)
                    )
                
                # Sample duplicates
                samples = duplicate_analysis.get('sample_duplicates', [])
                if samples:
                    with st.expander("View Sample Duplicate Groups"):
                        for i, sample in enumerate(samples, 1):
                            st.markdown(f"**Group {i}:** {sample['count']} duplicate rows")
                            if sample.get('rows'):
                                st.dataframe(
                                    pd.DataFrame(sample['rows']),
                                    use_container_width=True
                                )
            else:
                st.success("✅ No duplicate rows detected!")
        
        with tab3:
            st.markdown("#### Outlier Analysis")
            outlier_analysis = report.get('outliers', {})
            
            if outlier_analysis.get('total_outliers', 0) > 0:
                render_outliers_boxplot(outlier_analysis)
                
                st.markdown(f"**Method Used:** {outlier_analysis.get('method', 'N/A').upper()}")
                
                # Outlier details table
                details = outlier_analysis.get('details', [])
                outlier_cols = [d for d in details if d.get('outlier_count', 0) > 0]
                
                if outlier_cols:
                    st.markdown("**Outlier Details:**")
                    
                    for detail in outlier_cols[:5]:  # Show top 5
                        with st.expander(f"{detail['column']} - {detail['outlier_count']} outliers ({detail['outlier_percentage']}%)"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Statistics:**")
                                stats = detail.get('statistics', {})
                                st.write(f"- Mean: {stats.get('mean', 0):.2f}")
                                st.write(f"- Median: {stats.get('median', 0):.2f}")
                                st.write(f"- Std Dev: {stats.get('std', 0):.2f}")
                            
                            with col2:
                                st.write("**Bounds:**")
                                if detail.get('lower_bound') is not None:
                                    st.write(f"- Lower: {detail['lower_bound']:.2f}")
                                    st.write(f"- Upper: {detail['upper_bound']:.2f}")
                            
                            if detail.get('sample_outliers'):
                                st.write("**Sample Outliers:**")
                                st.write(detail['sample_outliers'][:10])
            else:
                st.success("✅ No outliers detected!")
        
        with tab4:
            st.markdown("#### Data Type Distribution")
            dataset_info = report.get('dataset_info', {})
            render_data_type_distribution(dataset_info)
            
            # Data type table
            with st.expander("View All Column Types"):
                dtypes = dataset_info.get('dtypes', {})
                if dtypes:
                    df_dtypes = pd.DataFrame([
                        {'Column': col, 'Data Type': dtype}
                        for col, dtype in dtypes.items()
                    ])
                    st.dataframe(df_dtypes, use_container_width=True)
        
        st.markdown("---")
        
        # Detailed Statistics
        st.markdown("### 📋 Detailed Statistics")
        render_detailed_stats(report)
        
        st.markdown("---")
        
        # Download Report
        st.markdown("### 💾 Download Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON download
            report_json = json.dumps(report, indent=2)
            st.download_button(
                label="📄 Download JSON Report",
                data=report_json,
                file_name=f"{report.get('report_id', 'quality_report')}.json",
                mime="application/json"
            )
        
        with col2:
            # Summary text download
            summary_text = f"""
Quality Report Summary
======================
Report ID: {report.get('report_id')}
Filename: {report.get('filename')}
Timestamp: {report.get('timestamp')}

Overall Quality Score: {score_result.get('overall_score', 0)}/100 ({score_result.get('grade', 'Unknown')})

Dataset Info:
- Rows: {dataset_info.get('rows', 0):,}
- Columns: {dataset_info.get('columns', 0)}

Issues:
- High Priority: {report.get('summary', {}).get('high_priority_issues', 0)}
- Medium Priority: {report.get('summary', {}).get('medium_priority_issues', 0)}
- Low Priority: {report.get('summary', {}).get('low_priority_issues', 0)}

Missing Values: {missing_analysis.get('overall_missing_percentage', 0)}%
Duplicates: {duplicate_analysis.get('duplicate_percentage', 0)}%
Outliers: {outlier_analysis.get('outlier_percentage', 0)}%
"""
            st.download_button(
                label="📝 Download Summary",
                data=summary_text,
                file_name=f"{report.get('report_id', 'quality_report')}_summary.txt",
                mime="text/plain"
            )
    
    else:
        st.info("👆 Select a file and run quality check to see results")


if __name__ == "__main__":
    st.set_page_config(
        page_title="Neural Watch - Quality Report",
        page_icon="📊",
        layout="wide"
    )
    
    render_quality_report_page()