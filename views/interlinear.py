"""
ScriptureLens - Interlinear View Page
"""

import streamlit as st
import pandas as pd
import sqlite3
import os

from utils import BIBLE_BOOKS, get_connection


def load_all_words_with_links(db_path, position_book, position_chapter):
    """Load all words with their alignment links for interlinear view."""
    conn = get_connection(db_path)
    
    # Source words with links
    source_query = """
    SELECT 
        w.id as word_id,
        w.text as source_text,
        w.position_verse,
        w.position_word,
        w.required as is_required,
        l.status,
        GROUP_CONCAT(tw.text, ' ') as target_text
    FROM words_or_parts w
    LEFT JOIN links__source_words lsw ON w.id = lsw.word_id
    LEFT JOIN links l ON lsw.link_id = l.id
    LEFT JOIN links__target_words ltw ON l.id = ltw.link_id
    LEFT JOIN words_or_parts tw ON ltw.word_id = tw.id
    WHERE w.side = 'sources'
      AND w.position_book = ?
      AND w.position_chapter = ?
    GROUP BY w.id
    ORDER BY w.position_verse, w.position_word
    """
    source_df = pd.read_sql_query(source_query, conn, params=[position_book, position_chapter])
    
    # Target words with links
    target_query = """
    SELECT 
        w.id as word_id,
        w.text as target_text,
        w.position_verse,
        w.position_word,
        sw.required as is_required,
        l.status,
        GROUP_CONCAT(sw.text, ' ') as source_text
    FROM words_or_parts w
    LEFT JOIN links__target_words ltw ON w.id = ltw.word_id
    LEFT JOIN links l ON ltw.link_id = l.id
    LEFT JOIN links__source_words lsw ON l.id = lsw.link_id
    LEFT JOIN words_or_parts sw ON lsw.word_id = sw.id
    WHERE w.side LIKE 'target%'
      AND w.position_book = ?
      AND w.position_chapter = ?
    GROUP BY w.id
    ORDER BY w.position_verse, w.position_word
    """
    target_df = pd.read_sql_query(target_query, conn, params=[position_book, position_chapter])
    
    return source_df, target_df


def render(project_name, db_path):
    """Interlinear view page with source/target alignment display."""
    st.title(f"📖 {project_name}")
    st.caption(f"Database: {os.path.basename(db_path)}")
    
    st.sidebar.markdown("---")
    st.sidebar.header("Interlinear Navigation")
    
    # Read URL query params if present
    query_params = st.query_params
    url_book = query_params.get("book")
    url_chapter = query_params.get("chapter")
    
    # Book selector
    book_order = {v: k for k, v in BIBLE_BOOKS.items()}
    book_names = list(BIBLE_BOOKS.values())
    
    # Set default book from URL param if available
    default_book_idx = 0
    if url_book:
        try:
            url_book_id = int(url_book)
            book_name_from_url = BIBLE_BOOKS.get(url_book_id)
            if book_name_from_url and book_name_from_url in book_names:
                default_book_idx = book_names.index(book_name_from_url)
        except ValueError:
            pass
    
    selected_book_name = st.sidebar.selectbox("Book", book_names, index=default_book_idx, key="il_book")
    selected_book_id = book_order.get(selected_book_name, 40)
    
    # Chapter selector - use URL param as default if available
    default_chapter = 1
    if url_chapter:
        try:
            default_chapter = int(url_chapter)
        except ValueError:
            pass
    
    selected_chapter = st.sidebar.number_input("Chapter", min_value=1, value=default_chapter, step=1, key="il_chap")
    
    # View mode selector
    view_mode = st.sidebar.radio("View by:", ["Source Order", "Target Order"], key="il_view")
    
    # Hide unlinked toggle
    hide_unlinked = st.sidebar.checkbox("Hide unlinked words", value=False, key="il_hide_unlinked")
    
    # Load data
    with st.spinner("Loading interlinear data..."):
        source_df, target_df = load_all_words_with_links(db_path, selected_book_id, selected_chapter)
    
    if source_df.empty and target_df.empty:
        st.warning(f"No words found for {selected_book_name} Chapter {selected_chapter}.")
        return
        
    # Display reference header
    st.subheader(f"{selected_book_name} {selected_chapter}")
    
    # Choose which dataframe to display based on view mode
    if view_mode == "Source Order":
        display_df = source_df.copy()
        display_df['Pos'] = display_df['position_word']
        display_df['Primary'] = display_df['source_text']
        display_df['Aligned'] = display_df['target_text'].fillna('')
        display_df['Req'] = display_df['is_required'].apply(lambda x: '✱' if x == 1 else '')
    else:
        display_df = target_df.copy()
        display_df['Pos'] = display_df['position_word']
        display_df['Primary'] = display_df['target_text']
        display_df['Aligned'] = display_df['source_text'].fillna('')
        display_df['Req'] = display_df['is_required'].apply(lambda x: '✱' if x == 1 else '')
    
    display_df['Status'] = display_df['status'].fillna('unlinked')
    
    # Filter unlinked if requested
    if hide_unlinked:
        display_df = display_df[display_df['Status'] != 'unlinked']
    
    # Group by verse
    verses = display_df.groupby('position_verse')
    
    for verse_num, verse_df in verses:
        # Get verse text from target words
        verse_words = target_df[target_df['position_verse'] == verse_num]['target_text'].dropna().unique()
        verse_text = ' '.join(verse_words) if len(verse_words) > 0 else ''
        
        # Verse Card Header
        st.markdown(f"""
        <div style="background:#f0f7ff; border-left:4px solid #2a6fc9; padding:10px; margin:10px 0; border-radius:5px;">
            <strong style="color:#2a6fc9;">Verse {verse_num}</strong><br/>
            <span style="font-size:1.0em;">{verse_text}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Build table
        table_df = verse_df[['Pos', 'Req', 'Primary', 'Aligned', 'Status']].drop_duplicates()
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
