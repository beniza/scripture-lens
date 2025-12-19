"""
ScriptureLens - Scripture Reader Page
Primary reading view for target language Scripture with source alignment info
"""

import streamlit as st
import pandas as pd

from utils import BIBLE_BOOKS, get_connection


@st.cache_data
def load_chapter_text(db_path, position_book, position_chapter):
    """Load target text for a chapter with alignment info."""
    conn = get_connection(db_path)
    
    query = """
    SELECT 
        tw.id as word_id,
        tw.text,
        tw.position_verse,
        tw.position_word,
        GROUP_CONCAT(sw.text, ' ') as source_text,
        GROUP_CONCAT(sw.lemma, ' ') as source_lemma,
        GROUP_CONCAT(sw.gloss, ' ') as source_gloss
    FROM words_or_parts tw
    LEFT JOIN links__target_words ltw ON tw.id = ltw.word_id
    LEFT JOIN links l ON ltw.link_id = l.id
    LEFT JOIN links__source_words lsw ON l.id = lsw.link_id
    LEFT JOIN words_or_parts sw ON lsw.word_id = sw.id
    WHERE tw.side LIKE 'target%'
      AND tw.position_book = ?
      AND tw.position_chapter = ?
    GROUP BY tw.id
    ORDER BY tw.position_verse, tw.position_word
    """
    
    df = pd.read_sql_query(query, conn, params=[position_book, position_chapter])
    return df


def render(project_name, db_path):
    """Scripture reader - clean reading view with optional alignment info."""
    
    # Session state
    if 'scr_chapter' not in st.session_state:
        st.session_state.scr_chapter = 1
    if 'scr_show_source' not in st.session_state:
        st.session_state.scr_show_source = False
    
    # === SIDEBAR ===
    with st.sidebar:
        st.markdown("#### 📜 Scripture")
        
        # Book
        book_names = list(BIBLE_BOOKS.values())
        book_order = {v: k for k, v in BIBLE_BOOKS.items()}
        selected_book = st.selectbox("Book", book_names, index=42, key="scr_book")
        book_id = book_order[selected_book]
        
        # Chapter nav
        col_p, col_c, col_n = st.columns([1, 2, 1])
        with col_p:
            if st.button("◀", key="scr_prev", use_container_width=True):
                if st.session_state.scr_chapter > 1:
                    st.session_state.scr_chapter -= 1
                    st.rerun()
        with col_c:
            chapter = st.number_input("Ch", min_value=1, 
                                     value=st.session_state.scr_chapter,
                                     key="scr_ch", label_visibility="collapsed")
            st.session_state.scr_chapter = chapter
        with col_n:
            if st.button("▶", key="scr_next", use_container_width=True):
                st.session_state.scr_chapter += 1
                st.rerun()
        
        st.divider()
        st.markdown("##### ⚙️ Display")
        show_source = st.toggle("Show source info", key="scr_src_toggle",
                               value=st.session_state.scr_show_source)
        st.session_state.scr_show_source = show_source
    
    # === MAIN CONTENT ===
    # Header
    st.markdown(f"## {selected_book} {chapter}")
    
    # Load data
    with st.spinner("Loading..."):
        df = load_chapter_text(db_path, book_id, chapter)
    
    if df.empty:
        st.warning(f"No text found for {selected_book} {chapter}")
        return
    
    # Group by verse and render
    verses = df.groupby('position_verse')
    
    for verse_num, verse_df in verses:
        verse_words = verse_df.sort_values('position_word')
        
        # Build verse HTML
        verse_html = f'<span style="font-weight:bold; color:#1976d2; margin-right:8px;">{verse_num}</span>'
        
        for _, word in verse_words.iterrows():
            text = word['text'] or ''
            source = word['source_text'] or ''
            lemma = word['source_lemma'] or ''
            gloss = word['source_gloss'] or ''
            
            # Tooltip
            tooltip_parts = []
            if source:
                tooltip_parts.append(source)
            if lemma:
                tooltip_parts.append(f"({lemma})")
            if gloss:
                tooltip_parts.append(f"- {gloss}")
            tooltip = " ".join(tooltip_parts) if tooltip_parts else "No alignment"
            
            # Word styling
            if source:
                style = "color:#333; cursor:pointer;"
            else:
                style = "color:#999; cursor:pointer;"
            
            verse_html += f'<span title="{tooltip}" style="{style}">{text} </span>'
        
        # Render verse
        st.markdown(f'''
        <div style="font-family: 'Gentium Plus', 'Noto Sans', serif; font-size:1.2em; line-height:1.8; margin-bottom:8px;">
            {verse_html}
        </div>
        ''', unsafe_allow_html=True)
        
        # Show source info if enabled
        if show_source:
            aligned_words = verse_df[verse_df['source_text'].notna()]
            if not aligned_words.empty:
                sources = []
                for _, w in aligned_words.iterrows():
                    sources.append(f"{w['text']} ← {w['source_text']}")
                st.caption(" | ".join(sources[:5]))  # Limit display
    
    # Footer
    st.divider()
    st.caption(f"{len(df)} words • {len(verses)} verses")
