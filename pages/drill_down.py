"""
ScriptureLens - Drill-down Analytics Page
"""

import streamlit as st
import plotly.express as px
import os

from utils import BIBLE_BOOKS


def render(df, project_name, db_path):
    """Drill-down analytics page with filters and KPIs."""
    st.title(f"🔍 {project_name}")
    st.caption(f"Database: {os.path.basename(db_path)}")
    
    # Sidebar Filters
    st.sidebar.markdown("---")
    st.sidebar.header("Drill-down Filters")
    
    testament_opt = ["All"] + sorted(df['testament'].unique().tolist())
    testament_sel = st.sidebar.selectbox("Division", testament_opt, key="dd_div")
    
    filtered_df = df.copy()
    if testament_sel != "All":
        filtered_df = filtered_df[filtered_df['testament'] == testament_sel]
        
    book_order = {v: k for k, v in BIBLE_BOOKS.items()}
    unique_books = filtered_df['book_name'].unique().tolist()
    sorted_books = sorted(unique_books, key=lambda x: book_order.get(x, 999))
    
    book_opt = ["All"] + sorted_books
    book_sel = st.sidebar.selectbox("Book", book_opt, key="dd_book")
    
    if book_sel != "All":
        filtered_df = filtered_df[filtered_df['book_name'] == book_sel]
        
    chapter_opt = ["All"] + sorted(filtered_df['position_chapter'].unique().tolist())
    chapter_sel = st.sidebar.selectbox("Chapter", chapter_opt, key="dd_chap")
    
    if chapter_sel != "All":
        filtered_df = filtered_df[filtered_df['position_chapter'] == chapter_sel]
        
    verse_opt = ["All"] + sorted(filtered_df['position_verse'].unique().tolist())
    verse_sel = st.sidebar.selectbox("Verse", verse_opt, key="dd_verse")
    
    if verse_sel != "All":
        filtered_df = filtered_df[filtered_df['position_verse'] == verse_sel]

    status_opt = ["All"] + sorted(df['status'].unique().tolist())
    status_sel = st.sidebar.selectbox("Status", status_opt, key="dd_stat")
    if status_sel != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_sel]

    # KPI Metrics
    total_links = len(filtered_df)
    req_links = len(filtered_df[filtered_df['is_required'] == 1])
    approved = len(filtered_df[filtered_df['status'] == 'approved'])
    created = len(filtered_df[filtered_df['status'] == 'created'])
    rejected = len(filtered_df[filtered_df['status'] == 'rejected'])
    
    comp_count = approved + created
    req_comp_count = len(filtered_df[(filtered_df['is_required'] == 1) & (filtered_df['status'].isin(['approved', 'created']))])
    
    pct_req = (req_comp_count / req_links * 100) if req_links > 0 else 0
    pct_total = (comp_count / total_links * 100) if total_links > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Links", f"{total_links:,}")
    col2.metric("Required Links", f"{req_links:,}")
    col3.metric("Approved", f"{approved:,}")
    col4.metric("Created", f"{created:,}")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Rejected", f"{rejected:,}")
    col_b.metric("% Compl. Required", f"{pct_req:.1f}%")
    col_c.metric("% Compl. Total", f"{pct_total:.1f}%")

    st.markdown("---")
    
    st.subheader(f"Status Distribution (Total Required: {req_links:,})")
    status_counts = filtered_df['status'].value_counts().reset_index()
    fig_status = px.pie(status_counts, values='count', names='status', hole=0.4,
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_status, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Detailed Links Data")
    
    # Sorting canonically (Book, Chap, Verse, Source Pos, Target Pos)
    display_df = filtered_df.sort_values(['position_book', 'position_chapter', 'position_verse', 'min_src_pos', 'min_tgt_pos'])
    
    # Reordering columns
    col_order = ['book_name', 'position_chapter', 'position_verse', 'source_text', 'target_text', 'status', 'min_src_pos', 'min_tgt_pos']
    display_df = display_df[col_order].rename(columns={
        'book_name': 'Book',
        'position_chapter': 'Chapter',
        'position_verse': 'Verse',
        'source_text': 'Source Text',
        'target_text': 'Target Text',
        'status': 'Status',
        'min_src_pos': 'Source Pos',
        'min_tgt_pos': 'Target Pos'
    })
    
    st.dataframe(display_df.head(500), use_container_width=True, hide_index=True)
