"""
ScriptureLens - BibleHub-Style Interlinear View
Displays words in vertical stacks with lemma, gloss, and translation
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json

from utils import BIBLE_BOOKS, get_connection


@st.cache_data
def load_interlinear_data(project_id, db_path, position_book, position_chapter):
    """Load interlinear data from SQLite or JSON fallback."""
    if db_path and Path(db_path).exists():
        return _load_interlinear_sqlite(db_path, position_book, position_chapter)
    return _load_interlinear_json(project_id, position_book, position_chapter, reverse=False)


def _load_interlinear_sqlite(db_path, position_book, position_chapter):
    conn = get_connection(db_path)
    query = """
    SELECT 
        sw.id as source_id,
        sw.text as source_text,
        sw.lemma,
        sw.gloss,
        sw.normalized_text,
        sw.position_verse,
        sw.position_word,
        l.status,
        GROUP_CONCAT(tw.text, ' ') as target_text
    FROM words_or_parts sw
    LEFT JOIN links__source_words lsw ON sw.id = lsw.word_id
    LEFT JOIN links l ON lsw.link_id = l.id
    LEFT JOIN links__target_words ltw ON l.id = ltw.link_id
    LEFT JOIN words_or_parts tw ON ltw.word_id = tw.id
    WHERE sw.side = 'sources'
      AND sw.position_book = ?
      AND sw.position_chapter = ?
    GROUP BY sw.id
    ORDER BY sw.position_verse, sw.position_word
    """
    return pd.read_sql_query(query, conn, params=[position_book, position_chapter])


@st.cache_data
def load_reverse_interlinear_data(project_id, db_path, position_book, position_chapter):
    """Load reverse interlinear data from SQLite or JSON fallback."""
    if db_path and Path(db_path).exists():
        return _load_reverse_interlinear_sqlite(db_path, position_book, position_chapter)
    return _load_interlinear_json(project_id, position_book, position_chapter, reverse=True)


def _load_reverse_interlinear_sqlite(db_path, position_book, position_chapter):
    conn = get_connection(db_path)
    query = """
    SELECT 
        tw.id as target_id,
        tw.text as target_text,
        tw.position_verse,
        tw.position_word as target_position,
        sw.text as source_text,
        sw.lemma,
        sw.gloss,
        l.status
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
    return pd.read_sql_query(query, conn, params=[position_book, position_chapter])


def _load_interlinear_json(project_id, position_book, position_chapter, reverse=False):
    """Fallback JSON loader for interlinear data."""
    from utils import APP_DATA_DIR
    
    # Load alignments
    align_file = None
    align_dir = APP_DATA_DIR / "alignments" / project_id
    for f in align_dir.glob(f"{position_book}_*.json"):
        align_file = f
        break
        
    if not align_file or not align_file.exists():
        if reverse:
            return pd.DataFrame(columns=['target_id', 'target_text', 'position_verse', 'target_position', 'source_text', 'lemma', 'gloss', 'status'])
        else:
            return pd.DataFrame(columns=['source_id', 'source_text', 'lemma', 'gloss', 'normalized_text', 'position_verse', 'position_word', 'status', 'target_text'])
        
    with open(align_file, 'r', encoding='utf-8') as f:
        align_data = json.load(f)
        
    records = []
    if reverse:
        target_file = APP_DATA_DIR / "targets" / project_id / align_file.name
        if not target_file.exists():
            return pd.DataFrame(columns=['target_id', 'target_text', 'position_verse', 'target_position', 'source_text', 'lemma', 'gloss', 'status'])
        with open(target_file, 'r', encoding='utf-8') as f:
            target_data = json.load(f)
            
        align_map = {}
        for rec in align_data.get('records', []):
            for t_id in rec.get('targetIds', []):
                align_map[t_id] = rec
                
        for ch in target_data.get('chapters', []):
            if ch.get('chapter') != position_chapter: continue
            for vs in ch.get('verses', []):
                v_num = vs.get('verse')
                for w in vs.get('words', []):
                    w_id = w.get('id')
                    align = align_map.get(w_id, {})
                    records.append({
                        'target_id': w_id,
                        'target_text': w.get('text'),
                        'position_verse': v_num,
                        'target_position': w.get('position'),
                        'source_text': ' '.join(align.get('sourceText', [])),
                        'lemma': '',
                        'gloss': '',
                        'status': align.get('status', '')
                    })
        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame(columns=['target_id', 'target_text', 'position_verse', 'target_position', 'source_text', 'lemma', 'gloss', 'status'])
        return df
    else:
        # Standard interlinear - reconstruct from alignments
        src_map = {}
        for rec in align_data.get('records', []):
            for s_id in rec.get('sourceIds', []):
                parts = s_id.split(':')[-1]
                if len(parts) >= 9:
                    ch = int(parts[3:6])
                    if ch != position_chapter: continue
                    v = int(parts[6:9])
                    pos = int(parts[9:12])
                    src_map[s_id] = {
                        'source_id': s_id,
                        'source_text': ' '.join(rec.get('sourceText', [])),
                        'lemma': '',
                        'gloss': '',
                        'normalized_text': '',
                        'position_verse': v,
                        'position_word': pos,
                        'status': rec.get('status'),
                        'target_text': ' '.join(rec.get('targetText', []))
                    }
        df = pd.DataFrame(src_map.values())
        if df.empty:
            return pd.DataFrame(columns=['source_id', 'source_text', 'lemma', 'gloss', 'normalized_text', 'position_verse', 'position_word', 'status', 'target_text'])
        return df.sort_values(['position_verse', 'position_word'])


def render(project_name, db_path):
    """BibleHub-style interlinear view using native Streamlit."""
    
    # Initialize session state
    if 'il2_chapter_val' not in st.session_state:
        st.session_state.il2_chapter_val = 1
    if 'il2_reverse' not in st.session_state:
        st.session_state.il2_reverse = False
    if 'il2_words_per_row' not in st.session_state:
        st.session_state.il2_words_per_row = 8
    
    # === SIDEBAR: Page-specific controls ===
    with st.sidebar:
        st.markdown("#### 📖 Interlinear")
        
        # Book selection
        book_names = list(BIBLE_BOOKS.values())
        book_order = {v: k for k, v in BIBLE_BOOKS.items()}
        selected_book = st.selectbox("Book", book_names, index=42, key="il2_book")
        book_id = book_order[selected_book]
        
        # Chapter with prev/next
        col_prev, col_ch, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("◀", key="il2_prev", use_container_width=True):
                if st.session_state.il2_chapter_val > 1:
                    st.session_state.il2_chapter_val -= 1
                    st.rerun()
        with col_ch:
            chapter = st.number_input(
                "Chapter", min_value=1, 
                value=st.session_state.il2_chapter_val, 
                key="il2_chapter",
                label_visibility="collapsed"
            )
            st.session_state.il2_chapter_val = chapter
        with col_next:
            if st.button("▶", key="il2_next", use_container_width=True):
                st.session_state.il2_chapter_val += 1
                st.rerun()
        
        st.divider()
        
        # Display settings
        st.markdown("##### ⚙️ Display")
        reverse = st.toggle("🔄 Reverse Interlinear", key="il2_reverse_toggle", 
                           value=st.session_state.il2_reverse, 
                           help="Show target language first")
        st.session_state.il2_reverse = reverse
        
        # Layout toggle
        if 'il2_layout' not in st.session_state:
            st.session_state.il2_layout = "Card"
        layout = st.radio("Layout", ["Card", "Grid"], 
                         index=0 if st.session_state.il2_layout == "Card" else 1,
                         horizontal=True, key="il2_layout_radio")
        st.session_state.il2_layout = layout
        
        words_per_row = st.slider("Words per row", 4, 12, 
                                  st.session_state.il2_words_per_row, 
                                  key="il2_wpr")
        st.session_state.il2_words_per_row = words_per_row
    
    # Load data based on mode
    with st.spinner("Loading..."):
        if reverse:
            df = load_reverse_interlinear_data(project_name, db_path, book_id, chapter)
        else:
            df = load_interlinear_data(project_name, db_path, book_id, chapter)
    
    if df.empty:
        st.warning(f"No data found for {selected_book} {chapter}")
        return
    
    # Header with word count
    mode = "↔️ Reverse" if reverse else ""
    st.caption(f"**{selected_book} {chapter}** • {len(df)} words {mode}")
    
    # Group by verse
    verses = df.groupby('position_verse')
    
    layout = st.session_state.il2_layout
    
    for verse_num, verse_df in verses:
        with st.container():
            st.markdown(f"**Verse {verse_num}**")
            
            words_list = verse_df.to_dict('records')
            row_size = st.session_state.il2_words_per_row
            
            if layout == "Grid":
                # Grid layout - compact table-like view
                grid_html = '<div style="display:flex; flex-wrap:wrap; gap:2px;">'
                for word in words_list:
                    source = word.get('source_text', '') or ''
                    lemma = word.get('lemma', '') or ''
                    gloss = word.get('gloss', '') or ''
                    target = word.get('target_text', '') or ''
                    
                    # Build tooltip
                    tooltip_parts = []
                    if lemma:
                        tooltip_parts.append(f"Lemma: {lemma}")
                    if gloss:
                        tooltip_parts.append(f"Gloss: {gloss}")
                    if target:
                        tooltip_parts.append(f"→ {target}")
                    else:
                        tooltip_parts.append("(No alignment)")
                    tooltip = " | ".join(tooltip_parts)
                    
                    aligned_style = "border:2px solid #81c784;" if target else "border:1px dashed #ccc;"
                    
                    if reverse:
                        grid_html += f'''
                        <div title="{tooltip}" style="text-align:center; padding:4px 6px; background:#e8f5e9; border-radius:4px; min-width:50px; cursor:pointer; {aligned_style}">
                            <div style="font-size:1em; font-weight:bold; color:#2e7d32;">{target if target else '—'}</div>
                            <div style="font-size:0.7em; color:#1565c0;">{source}</div>
                        </div>'''
                    else:
                        grid_html += f'''
                        <div title="{tooltip}" style="text-align:center; padding:4px 6px; background:#f8f9fa; border-radius:4px; min-width:50px; cursor:pointer; {aligned_style}">
                            <div style="font-size:1em; font-weight:bold; color:#1565c0;">{source}</div>
                            <div style="font-size:0.7em; color:#2e7d32;">{target if target else ''}</div>
                        </div>'''
                grid_html += '</div>'
                st.markdown(grid_html, unsafe_allow_html=True)
            else:
                # Card layout - detailed view
                for i in range(0, len(words_list), row_size):
                    row_words = words_list[i:i+row_size]
                    cols = st.columns(len(row_words))
                    
                    for idx, word in enumerate(row_words):
                        with cols[idx]:
                            source = word.get('source_text', '') or ''
                            lemma = word.get('lemma', '') or ''
                            gloss = word.get('gloss', '') or ''
                            target = word.get('target_text', '') or ''
                            
                            # Tooltip for card
                            tooltip = f"Source: {source}"
                            if lemma:
                                tooltip += f" | Lemma: {lemma}"
                            if target:
                                tooltip += f" | Aligned → {target}"
                            else:
                                tooltip += " | ⚠ Not aligned"
                            
                            # Border style for aligned/unaligned
                            border = "border-left:4px solid #81c784;" if target else "border-left:4px solid #ffcc80;"
                            
                            if reverse:
                                st.markdown(f"""
<div title="{tooltip}" style="text-align:center; padding:8px; background:#e8f5e9; border-radius:8px; {border} margin:4px; cursor:pointer;">
<div style="font-size:1.3em; font-weight:bold; color:#2e7d32;">{target if target else '—'}</div>
<div style="font-size:0.85em; color:#333;">{gloss}</div>
<div style="font-size:0.8em; color:#1565c0; background:#e3f2fd; padding:2px 4px; border-radius:4px; margin-top:4px;">{source}</div>
<div style="font-size:0.75em; color:#666; font-style:italic;">{lemma}</div>
</div>
""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
<div title="{tooltip}" style="text-align:center; padding:8px; background:#f8f9fa; border-radius:8px; {border} margin:4px; cursor:pointer;">
<div style="font-size:1.3em; font-weight:bold; color:#1565c0;">{source}</div>
<div style="font-size:0.8em; color:#666; font-style:italic;">{lemma}</div>
<div style="font-size:0.85em; color:#333;">{gloss}</div>
{f'<div style="font-size:0.8em; color:#2e7d32; background:#e8f5e9; padding:2px 4px; border-radius:4px; margin-top:4px;">{target}</div>' if target else '<div style="font-size:0.75em; color:#f57c00;">⚠ unaligned</div>'}
</div>
""", unsafe_allow_html=True)
            
            st.divider()
    
    # Legend
    with st.expander("📋 Legend"):
        if reverse:
            st.markdown("🟢 **Green** = Target | 🔵 **Blue** = Source")
        else:
            st.markdown("🔵 **Blue** = Source | 🟢 **Green** = Target")
