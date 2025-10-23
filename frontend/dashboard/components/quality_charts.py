"""
Quality Charts Component for Neural Watch
Phase 2: Data Quality Checks
Visualization components for quality reports
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List


def render_quality_score_gauge(score: float, grade: str):
    """
    Render quality score gauge chart
    
    Args:
        score: Quality score (0-100)
        grade: Quality grade
    """
    # Determine color based on score
    if score >= 90:
        color = "green"
    elif score >= 70:
        color = "yellow"
    elif score >= 50:
        color = "orange"
    else:
        color = "red"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Quality Score<br><span style='font-size:0.8em'>{grade}</span>"},
        delta={'reference': 80, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 70], 'color': "lightyellow"},
                {'range': [70, 90], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_missing_values_chart(missing_analysis: Dict):
    """
    Render missing values bar chart
    
    Args:
        missing_analysis: Missing value analysis results
    """
    details = missing_analysis.get('details', [])
    
    if not details:
        st.info("✅ No missing values detected!")
        return
    
    # Create DataFrame for plotting
    df = pd.DataFrame(details)
    df = df.sort_values('missing_percentage', ascending=True)
    
    # Create bar chart
    fig = px.bar(
        df,
        x='missing_percentage',
        y='column',
        orientation='h',
        color='severity',
        color_discrete_map={
            'low': 'green',
            'medium': 'orange',
            'high': 'red'
        },
        title='Missing Values by Column',
        labels={'missing_percentage': 'Missing %', 'column': 'Column'}
    )
    
    fig.update_layout(height=max(300, len(details) * 30))
    st.plotly_chart(fig, use_container_width=True)


def render_missing_heatmap(df: pd.DataFrame, sample_size: int = 50):
    """
    Render missing values heatmap
    
    Args:
        df: DataFrame to visualize
        sample_size: Number of rows to sample
    """
    # Sample data if too large
    if len(df) > sample_size:
        df_sample = df.sample(n=sample_size, random_state=42)
    else:
        df_sample = df
    
    # Create binary missing matrix
    missing_matrix = df_sample.isnull().astype(int)
    
    # Create heatmap
    fig = px.imshow(
        missing_matrix.T,
        labels=dict(x="Row", y="Column", color="Missing"),
        x=missing_matrix.index,
        y=missing_matrix.columns,
        color_continuous_scale=["lightblue", "red"],
        title=f'Missing Values Heatmap (Sample of {len(df_sample)} rows)'
    )
    
    fig.update_layout(height=max(400, len(df_sample.columns) * 20))
    fig.update_xaxes(showticklabels=False)
    
    st.plotly_chart(fig, use_container_width=True)


def render_outliers_boxplot(outlier_analysis: Dict, df: pd.DataFrame = None):
    """
    Render box plots for columns with outliers
    
    Args:
        outlier_analysis: Outlier analysis results
        df: Original DataFrame (optional, for plotting)
    """
    details = outlier_analysis.get('details', [])
    columns_with_outliers = [d for d in details if d['outlier_count'] > 0]
    
    if not columns_with_outliers:
        st.info("✅ No outliers detected!")
        return
    
    # Create DataFrame for plotting
    plot_data = []
    for detail in columns_with_outliers[:5]:  # Limit to top 5
        plot_data.append({
            'column': detail['column'],
            'outlier_count': detail['outlier_count'],
            'outlier_percentage': detail['outlier_percentage'],
            'severity': detail['severity']
        })
    
    df_plot = pd.DataFrame(plot_data)
    
    # Create bar chart
    fig = px.bar(
        df_plot,
        x='column',
        y='outlier_count',
        color='severity',
        color_discrete_map={
            'low': 'green',
            'medium': 'orange',
            'high': 'red'
        },
        title='Outlier Count by Column',
        labels={'outlier_count': 'Outlier Count', 'column': 'Column'}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_duplicate_pie_chart(duplicate_analysis: Dict):
    """
    Render pie chart for duplicate vs unique rows
    
    Args:
        duplicate_analysis: Duplicate analysis results
    """
    total_rows = duplicate_analysis.get('total_rows', 0)
    total_duplicates = duplicate_analysis.get('total_duplicates', 0)
    unique_rows = duplicate_analysis.get('unique_rows', 0)
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=['Unique Rows', 'Duplicate Rows'],
        values=[unique_rows, total_duplicates],
        hole=0.4,
        marker_colors=['lightblue', 'red']
    )])
    
    fig.update_layout(
        title='Duplicate vs Unique Rows',
        annotations=[dict(text=f'{total_rows}<br>Total', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_score_breakdown(score_result: Dict):
    """
    Render score breakdown chart
    
    Args:
        score_result: Quality score results
    """
    breakdown = score_result.get('breakdown', {})
    
    categories = []
    scores = []
    weights = []
    
    for category, data in breakdown.items():
        categories.append(category.replace('_', ' ').title())
        scores.append(data['score'])
        weights.append(data['weight'])
    
    # Create grouped bar chart
    fig = go.Figure(data=[
        go.Bar(name='Score', x=categories, y=scores, marker_color='lightblue'),
        go.Bar(name='Weight %', x=categories, y=weights, marker_color='lightgreen')
    ])
    
    fig.update_layout(
        title='Quality Score Breakdown',
        xaxis_title='Category',
        yaxis_title='Value',
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_data_type_distribution(dataset_info: Dict):
    """
    Render data type distribution pie chart
    
    Args:
        dataset_info: Dataset information
    """
    dtypes = dataset_info.get('dtypes', {})
    
    # Count data types
    dtype_counts = {}
    for dtype in dtypes.values():
        dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
    
    # Create pie chart
    fig = px.pie(
        values=list(dtype_counts.values()),
        names=list(dtype_counts.keys()),
        title='Data Type Distribution'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_quality_trend(reports: List[Dict]):
    """
    Render quality score trend over time
    
    Args:
        reports: List of quality reports
    """
    if len(reports) < 2:
        st.info("Need at least 2 reports to show trends")
        return
    
    # Extract data
    timestamps = [r['timestamp'] for r in reports]
    scores = [r.get('quality_score', {}).get('overall_score', 0) for r in reports]
    
    # Create line chart
    fig = go.Figure(data=go.Scatter(
        x=timestamps,
        y=scores,
        mode='lines+markers',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Quality Score Trend',
        xaxis_title='Timestamp',
        yaxis_title='Quality Score',
        yaxis_range=[0, 100],
        height=400
    )
    
    # Add horizontal line at 70 (Good threshold)
    fig.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Good Threshold")
    
    st.plotly_chart(fig, use_container_width=True)