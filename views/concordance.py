"""
ScriptureLens - Concordance V3 Page
"""

import streamlit as st
import pandas as pd

from utils import BIBLE_BOOKS, get_connection


@st.cache_data
def load_lemmas_with_gloss(db_path, testament='NT', limit=100):
    """Load lemmas with glosses for NT (default) or OT."""
    conn = get_connection(db_path)
    
    # NT: books 40-66, OT: books 1-39
    if testament == 'NT':
        book_filter = "position_book >= 40"
    else:
        book_filter = "position_book <= 39"
    
    query = f"""
    SELECT 
        lemma,
        MAX(gloss) as gloss,
        COUNT(DISTINCT id) as frequency
    FROM words_or_parts
    WHERE side = 'sources' 
      AND required = 1
      AND lemma IS NOT NULL
      AND lemma != ''
      AND {book_filter}
    GROUP BY lemma
    ORDER BY frequency DESC
    LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=[limit])
    return df


@st.cache_data  
def load_renderings_for_lemma(db_path, lemma, testament='NT'):
    """Load target renderings for a specific lemma."""
    conn = get_connection(db_path)
    
    if testament == 'NT':
        book_filter = "sw.position_book >= 40"
    else:
        book_filter = "sw.position_book <= 39"
    
    query = f"""
    SELECT 
        tw.normalized_text as rendering,
        tw.text as surface_form,
        COUNT(DISTINCT sw.id) as frequency
    FROM words_or_parts sw
    JOIN links__source_words lsw ON sw.id = lsw.word_id
    JOIN links l ON lsw.link_id = l.id
    JOIN links__target_words ltw ON l.id = ltw.link_id
    JOIN words_or_parts tw ON ltw.word_id = tw.id
    WHERE sw.lemma = ?
      AND sw.side = 'sources'
      AND sw.required = 1
      AND {book_filter}
    GROUP BY tw.normalized_text
    ORDER BY frequency DESC
    LIMIT 50
    """
    
    df = pd.read_sql_query(query, conn, params=[lemma])
    return df


@st.cache_data
def load_verses_for_rendering(db_path, lemma, rendering, testament='NT', context_size=5):
    """Load verses where a lemma is rendered with a specific target word."""
    conn = get_connection(db_path)
    
    if testament == 'NT':
        book_filter = "sw.position_book >= 40"
    else:
        book_filter = "sw.position_book <= 39"
    
    # Get occurrences where this lemma is linked to this rendering
    query = f"""
    SELECT DISTINCT
        sw.id as source_word_id,
        tw.id as target_word_id,
        tw.text as target_text,
        tw.position_book,
        tw.position_chapter,
        tw.position_verse,
        tw.position_word
    FROM words_or_parts sw
    JOIN links__source_words lsw ON sw.id = lsw.word_id
    JOIN links l ON lsw.link_id = l.id
    JOIN links__target_words ltw ON l.id = ltw.link_id
    JOIN words_or_parts tw ON ltw.word_id = tw.id
    WHERE sw.lemma = ?
      AND tw.normalized_text = ?
      AND sw.side = 'sources'
      AND sw.required = 1
      AND {book_filter}
    ORDER BY tw.position_book, tw.position_chapter, tw.position_verse
    LIMIT 30
    """
    
    occurrences = pd.read_sql_query(query, conn, params=[lemma, rendering])
    
    if occurrences.empty:
        return []
    
    # Get unique verses
    verse_keys = occurrences[['position_book', 'position_chapter', 'position_verse']].drop_duplicates()
    
    conditions = []
    params = []
    for _, row in verse_keys.iterrows():
        conditions.append("(position_book = ? AND position_chapter = ? AND position_verse = ?)")
        params.extend([int(row['position_book']), int(row['position_chapter']), int(row['position_verse'])])
    
    # Get all target words for these verses
    verse_query = f"""
    SELECT id, text, position_book, position_chapter, position_verse, position_word
    FROM words_or_parts 
    WHERE side LIKE 'target%'
      AND ({' OR '.join(conditions)})
    ORDER BY position_book, position_chapter, position_verse, position_word
    """
    
    all_words = pd.read_sql_query(verse_query, conn, params=params)
    
    # Build verse contexts
    results = []
    for _, occ in occurrences.iterrows():
        book = int(occ['position_book'])
        chapter = int(occ['position_chapter'])
        verse = int(occ['position_verse'])
        target_pos = int(occ['position_word'])
        
        verse_words = all_words[
            (all_words['position_book'] == book) & 
            (all_words['position_chapter'] == chapter) & 
            (all_words['position_verse'] == verse)
        ].sort_values('position_word')
        
        if verse_words.empty:
            continue
        
        words_list = verse_words['text'].tolist()
        positions = verse_words['position_word'].tolist()
        
        try:
            target_idx = positions.index(target_pos)
        except ValueError:
            continue
        
        start_idx = max(0, target_idx - context_size)
        end_idx = min(len(words_list), target_idx + context_size + 1)
        
        before = ' '.join(words_list[start_idx:target_idx])
        keyword = words_list[target_idx]
        after = ' '.join(words_list[target_idx + 1:end_idx])
        
        results.append({
            'reference': f"{BIBLE_BOOKS.get(book, '')} {chapter}:{verse}",
            'before': before,
            'keyword': keyword,
            'after': after,
            'book': book,
            'chapter': chapter
        })
    
    return results


def render(project_name, db_path):
    """Concordance V3 - Optimized lazy-load design with NT/Greek focus."""
    
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        [data-testid="column"] { width: 100% !important; margin-bottom: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title(f"📚 Concordance - {project_name}")
    
    # Initialize session state
    if 'cv3_selected_lemma' not in st.session_state:
        st.session_state.cv3_selected_lemma = None
    if 'cv3_selected_rendering' not in st.session_state:
        st.session_state.cv3_selected_rendering = None
    
    # === SIDEBAR: Page-specific controls ===
    with st.sidebar:
        st.markdown("#### 📚 Concordance")
        
        # Testament toggle
        testament = st.radio("Testament", ["NT (Greek)", "OT (Hebrew)"], 
                            key="cv3_testament", horizontal=True)
        testament_code = 'NT' if 'NT' in testament else 'OT'
        
        st.divider()
        st.markdown("##### ⚙️ Display")
        
        # Lemma limit
        lemma_limit = st.slider("Max lemmas", 50, 500, 100, 50, key="cv3_limit")
        
        # Context size
        context_size = st.slider("Context words", 3, 10, 5, key="cv3_context")
    
    # Load lemmas with glosses
    with st.spinner("Loading lemmas..."):
        lemmas_df = load_lemmas_with_gloss(db_path, testament_code, lemma_limit)
    
    if lemmas_df.empty:
        st.warning("No lemmas found for selected testament.")
        return
    
    st.caption(f"**{len(lemmas_df)} lemmas** loaded from {testament}")
    
    # 3-Column Layout (1:1:3)
    col1, col2, col3 = st.columns([1, 1, 3])
    
    # Column 1: Lemmas with Gloss
    with col1:
        st.markdown("### Lemmas")
        with st.container(height=550):
            for idx, row in lemmas_df.iterrows():
                lemma = row['lemma']
                gloss = row['gloss'] if pd.notna(row['gloss']) else ''
                freq = row['frequency']
                is_selected = st.session_state.cv3_selected_lemma == lemma
                
                # Display lemma with gloss
                label = f"{'► ' if is_selected else ''}{lemma}"
                if gloss:
                    label += f" ({gloss})"
                label += f" [{freq}]"
                
                if st.button(label, key=f"cv3_lem_{idx}", use_container_width=True,
                            type="primary" if is_selected else "secondary"):
                    st.session_state.cv3_selected_lemma = lemma
                    st.session_state.cv3_selected_rendering = None
                    st.rerun()
    
    # Column 2: Renderings (lazy-loaded)
    with col2:
        st.markdown("### Renderings")
        selected_lemma = st.session_state.cv3_selected_lemma
        
        if selected_lemma:
            with st.container(height=550):
                renderings_df = load_renderings_for_lemma(db_path, selected_lemma, testament_code)
                
                if renderings_df.empty:
                    st.info("No renderings found (unaligned)")
                else:
                    for idx, row in renderings_df.iterrows():
                        rendering = row['rendering']
                        freq = row['frequency']
                        is_sel = st.session_state.cv3_selected_rendering == rendering
                        
                        label = f"{'► ' if is_sel else ''}{rendering} ({freq})"
                        if st.button(label, key=f"cv3_rend_{idx}", use_container_width=True,
                                    type="primary" if is_sel else "secondary"):
                            st.session_state.cv3_selected_rendering = rendering
                            st.rerun()
        else:
            st.info("← Select a lemma")
    
    # Column 3: Verses (lazy-loaded)
    with col3:
        st.markdown("### Verses")
        selected_lemma = st.session_state.cv3_selected_lemma
        selected_rendering = st.session_state.cv3_selected_rendering
        
        if selected_lemma and selected_rendering:
            with st.container(height=550):
                verses = load_verses_for_rendering(
                    db_path, selected_lemma, selected_rendering, 
                    testament_code, context_size
                )
                
                if not verses:
                    st.info("No verses found")
                else:
                    st.caption(f"Showing {len(verses)} occurrences")
                    
                    for v in verses:
                        ref = v['reference']
                        before = v['before']
                        keyword = v['keyword']
                        after = v['after']
                        book_id = v['book']
                        chapter = v['chapter']
                        
                        st.markdown(f"""
                        <div style="background:#fafafa; border-left:3px solid #1976d2; padding:8px 12px; margin:4px 0; border-radius:4px;">
                            <strong>{ref}</strong>
                            <a href="interlinear?book={book_id}&chapter={chapter}" style="float:right; text-decoration:none;">📖</a>
                            <br/>
                            <span style="font-family: serif;">{before} <mark style="background:#fff59d; padding:2px 4px; border-radius:2px;"><strong>{keyword}</strong></mark> {after}</span>
                        </div>
                        """, unsafe_allow_html=True)
        elif selected_lemma:
            st.info("← Select a rendering")
        else:
            st.info("← Select a lemma first")
    
    # Status bar
    if selected_lemma:
        status = f"**Selected:** {selected_lemma}"
        if selected_rendering:
            status += f" → {selected_rendering}"
        st.markdown("---")
        st.markdown(status)
        
        # AI Word Study section
        render_ai_word_study(selected_lemma, testament_code)


def render_ai_word_study(lemma: str, testament: str):
    """Render AI-powered word study panel."""
    from utils.llm import LLMProvider, get_all_providers_status, generate_response
    from utils import load_settings
    
    settings = load_settings()
    providers = get_all_providers_status()
    configured = [p for p, c in providers.items() if c.is_configured]
    
    if not configured:
        return  # No LLM configured
    
    language = "Greek" if testament == "NT" else "Hebrew"
    
    st.markdown("---")
    st.subheader("🤖 AI Word Study")
    
    # Initialize session state for AI response
    if 'ai_word_study' not in st.session_state:
        st.session_state.ai_word_study = {}
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("✨ Generate", type="primary", use_container_width=True):
            # Get the configured provider (fallback to first configured)
            default_provider = settings.get("defaultLLMProvider", configured[0].value)
            try:
                provider = LLMProvider(default_provider)
            except ValueError:
                provider = configured[0]
            model = settings.get(f"llm_{provider.value}_model", "")
            
            system_prompt = f"""You are a Biblical scholar expert in {language} language and theology. 
Provide concise, insightful word studies for Bible translators and students.
Focus on: etymology, semantic range, theological significance, and translation considerations.
Keep responses under 300 words. Use markdown formatting."""

            prompt = f"""Provide a word study for the {language} word: **{lemma}**

Include:
1. **Definition** - Core meaning and etymology
2. **Semantic Range** - Different ways this word is used
3. **Theological Significance** - Key theological concepts
4. **Translation Tips** - How to translate accurately"""

            with st.spinner(f"Generating with {provider.value}..."):
                success, response = generate_response(
                    prompt=prompt,
                    provider=provider,
                    model=model,
                    system_prompt=system_prompt,
                    max_tokens=500,
                    temperature=0.7
                )
                
                if success:
                    st.session_state.ai_word_study[lemma] = response
                else:
                    st.session_state.ai_word_study[lemma] = f"❌ Error: {response}"
            
            st.rerun()
    
    with col2:
        # Show actual provider being used
        default_provider = settings.get("defaultLLMProvider", configured[0].value)
        st.caption(f"Using: {default_provider}")
    
    # Display response if available
    if lemma in st.session_state.ai_word_study:
        response = st.session_state.ai_word_study[lemma]
        if response.startswith("❌"):
            st.error(response)
        else:
            st.markdown(response)

