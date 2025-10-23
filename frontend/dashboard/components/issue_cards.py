"""
Issue Cards Component for Neural Watch
Phase 2: Data Quality Checks
Display quality issues with recommendations
"""
import streamlit as st
import pandas as pd
from typing import Dict, List


def render_issue_card(issue: Dict):
    """
    Render a single issue card
    
    Args:
        issue: Issue dictionary with priority, category, message, action
    """
    priority = issue.get('priority', 'low')
    category = issue.get('category', 'unknown')
    message = issue.get('message', 'No message')
    action = issue.get('action', 'no_action')
    
    # Determine styling based on priority
    if priority == 'high':
        emoji = "🔴"
        color = "#ffcccc"
        border_color = "#ff0000"
    elif priority == 'medium':
        emoji = "🟠"
        color = "#ffe6cc"
        border_color = "#ff9900"
    else:
        emoji = "🟢"
        color = "#ccffcc"
        border_color = "#00cc00"
    
    # Category emoji
    category_emoji_map = {
        'missing_values': "🔍",
        'duplicates': "📋",
        'outliers': "📊",
        'data_types': "🔤"
    }
    category_emoji = category_emoji_map.get(category, "⚠️")
    
    # Action descriptions
    action_descriptions = {
        'drop_column': "Consider dropping this column due to high missing percentage",
        'impute_median': "Impute missing values with median (numeric column, skewed distribution)",
        'impute_mean': "Impute missing values with mean (numeric column, normal distribution)",
        'impute_mode': "Impute missing values with mode (categorical column)",
        'forward_fill': "Forward fill missing values (time series data)",
        'keep_first': "Remove duplicates, keeping first occurrence",
        'review_and_remove': "Review duplicate rows and remove if appropriate",
        'investigate_cause': "Investigate root cause of duplicates",
        'winsorize': "Apply winsorization to clip outliers to bounds",
        'clip_bounds': "Clip outliers to calculated bounds",
        'transform_log': "Apply log transformation to reduce outlier impact",
        'investigate': "Investigate outliers manually",
        'no_action': "No action required"
    }
    
    action_description = action_descriptions.get(action, action.replace('_', ' ').title())
    
    # Render card
    with st.container():
        st.markdown(f"""
        <div style="
            background-color: {color};
            border-left: 5px solid {border_color};
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
        ">
            <h4>{emoji} {priority.upper()} Priority - {category_emoji} {category.replace('_', ' ').title()}</h4>
            <p><strong>Issue:</strong> {message}</p>
            <p><strong>Recommendation:</strong> {action_description}</p>
        </div>
        """, unsafe_allow_html=True)


def render_all_issues(recommendations: List[Dict]):
    """
    Render all issue cards
    
    Args:
        recommendations: List of recommendations
    """
    if not recommendations:
        st.success("✅ No quality issues detected! Your data looks great!")
        return
    
    # Group by priority
    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
    low_priority = [r for r in recommendations if r.get('priority') == 'low']
    
    # Display summary
    st.markdown(f"""
    ### 📋 Quality Issues Summary
    - 🔴 **High Priority**: {len(high_priority)}
    - 🟠 **Medium Priority**: {len(medium_priority)}
    - 🟢 **Low Priority**: {len(low_priority)}
    """)
    
    st.markdown("---")
    
    # Render high priority first
    if high_priority:
        st.markdown("### 🔴 High Priority Issues")
        for issue in high_priority:
            render_issue_card(issue)
    
    # Medium priority
    if medium_priority:
        st.markdown("### 🟠 Medium Priority Issues")
        for issue in medium_priority:
            render_issue_card(issue)
    
    # Low priority (collapsible)
    if low_priority:
        with st.expander(f"🟢 Low Priority Issues ({len(low_priority)})"):
            for issue in low_priority:
                render_issue_card(issue)


def render_summary_stats(quality_report: Dict):
    """
    Render summary statistics cards
    
    Args:
        quality_report: Quality report dictionary
    """
    missing = quality_report.get('missing_values', {})
    duplicates = quality_report.get('duplicates', {})
    outliers = quality_report.get('outliers', {})
    dataset_info = quality_report.get('dataset_info', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Rows",
            f"{dataset_info.get('rows', 0):,}",
            help="Total number of rows in dataset"
        )
    
    with col2:
        missing_pct = missing.get('overall_missing_percentage', 0)
        st.metric(
            "Missing Values",
            f"{missing_pct}%",
            delta=f"-{missing_pct}%" if missing_pct > 0 else None,
            delta_color="inverse",
            help="Percentage of missing values across all columns"
        )
    
    with col3:
        dup_pct = duplicates.get('duplicate_percentage', 0)
        st.metric(
            "Duplicates",
            f"{dup_pct}%",
            delta=f"-{dup_pct}%" if dup_pct > 0 else None,
            delta_color="inverse",
            help="Percentage of duplicate rows"
        )
    
    with col4:
        outlier_pct = outliers.get('outlier_percentage', 0)
        st.metric(
            "Outliers",
            f"{outlier_pct}%",
            delta=f"-{outlier_pct}%" if outlier_pct > 0 else None,
            delta_color="inverse",
            help="Percentage of outlier values in numeric columns"
        )


def render_detailed_stats(quality_report: Dict):
    """
    Render detailed statistics in expandable sections
    
    Args:
        quality_report: Quality report dictionary
    """
    # Missing Values Details
    missing = quality_report.get('missing_values', {})
    if missing.get('columns_affected', 0) > 0:
        with st.expander(f"🔍 Missing Values Details ({missing['columns_affected']} columns affected)"):
            details = missing.get('details', [])
            if details:
                df_missing = pd.DataFrame(details)
                st.dataframe(
                    df_missing[['column', 'missing_count', 'missing_percentage', 'severity', 'recommendation']],
                    use_container_width=True
                )
    
    # Duplicate Details
    duplicates = quality_report.get('duplicates', {})
    if duplicates.get('total_duplicates', 0) > 0:
        with st.expander(f"📋 Duplicate Details ({duplicates['total_duplicates']} duplicates found)"):
            st.write(f"**Duplicate Groups:** {duplicates.get('duplicate_groups', 0)}")
            st.write(f"**Recommendation:** {duplicates.get('recommendation', 'N/A').replace('_', ' ').title()}")
            
            samples = duplicates.get('sample_duplicates', [])
            if samples:
                st.write("**Sample Duplicate Groups:**")
                for i, sample in enumerate(samples[:3], 1):
                    st.write(f"Group {i}: {sample['count']} duplicate rows")
    
    # Outlier Details
    outliers = quality_report.get('outliers', {})
    if outliers.get('columns_with_outliers'):
        with st.expander(f"📊 Outlier Details ({len(outliers['columns_with_outliers'])} columns affected)"):
            details = outliers.get('details', [])
            outlier_data = [d for d in details if d.get('outlier_count', 0) > 0]
            
            if outlier_data:
                df_outliers = pd.DataFrame(outlier_data)
                st.dataframe(
                    df_outliers[['column', 'outlier_count', 'outlier_percentage', 'method', 'severity', 'recommendation']],
                    use_container_width=True
                )