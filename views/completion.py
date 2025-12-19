"""
ScriptureLens - Completion Overview Page
"""

import streamlit as st
import plotly.express as px
import os

from utils import load_completion_data


def render(df, project_name, db_path):
    """Completion overview page with charts and summary."""
    st.title(f"📊 {project_name}")
    if db_path:
        st.caption(f"Database: {os.path.basename(db_path)}")
    else:
        st.caption("Mode: Optimized JSON (Exported Data)")
    
    # Sidebar filter
    st.sidebar.markdown("---")
    st.sidebar.header("Completion Filters")
    testament_filter = st.sidebar.radio("Testament", ["All", "NT", "OT"], key="comp_testament")
    show_empty = st.sidebar.checkbox("Show books with 0%", value=True, key="comp_show_empty")
    
    comp_df = load_completion_data(project_name, db_path)
    
    # Apply testament filter
    if testament_filter == "NT":
        comp_df = comp_df[comp_df['position_book'] >= 40]
    elif testament_filter == "OT":
        comp_df = comp_df[comp_df['position_book'] <= 39]
    
    # Optionally hide books with 0% completion
    if not show_empty:
        comp_df = comp_df[comp_df['completed'] > 0]
    
    if comp_df.empty:
        st.warning("No books found matching the filter.")
        return

    # Visual Overview - Completion Percentage Bar Chart
    st.subheader("Completion Percentage by Book")
    fig_pct = px.bar(comp_df, x='book_name', y='Completion %', 
                     color='Completion %', color_continuous_scale='RdYlGn',
                     range_y=[0, 100],
                     category_orders={"book_name": comp_df['book_name'].tolist()})
    
    fig_pct.update_layout(xaxis_title="Book", yaxis_title="Completion %", height=300, 
                          margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_pct, use_container_width=True)

    # Link Status Distribution Chart
    st.markdown("---")
    st.subheader("Alignment Status Distribution by Book")
    
    # Aggregate data by book from main df
    book_stats = df.groupby(['position_book', 'book_name', 'status']).size().unstack(fill_value=0).reset_index()
    # Filter to only include books present in comp_df
    book_stats = book_stats[book_stats['book_name'].isin(comp_df['book_name'])]
    for status in ['approved', 'created', 'rejected', 'needsReview']:
        if status not in book_stats.columns:
            book_stats[status] = 0
            
    # Sorting by canonical order
    book_stats = book_stats.sort_values('position_book')

    plot_df = book_stats.melt(id_vars=['book_name'], value_vars=['approved', 'created', 'rejected', 'needsReview'],
                              var_name='Status', value_name='Count')
    
    fig_status = px.bar(plot_df, x='book_name', y='Count', color='Status',
                 color_discrete_map={
                     'approved': '#2ecc71', # Green
                     'created': '#3498db',  # Blue
                     'rejected': '#e74c3c', # Red
                     'needsReview': '#f1c40f' # Yellow
                 },
                 category_orders={"book_name": book_stats['book_name'].tolist()})
    
    fig_status.update_layout(xaxis_title="Book", yaxis_title="Number of Links", height=350, 
                             margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_status, use_container_width=True)

    # Summary Table
    st.subheader("Detailed Completion Summary")
    summary_df = comp_df[['book_name', 'total_required', 'completed', 'Completion %']]
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
