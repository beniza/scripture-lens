"""
ScriptureLens - Data Loading Utilities
"""

import streamlit as st
import sqlite3
import pandas as pd
import json
from pathlib import Path

from .constants import BIBLE_BOOKS, DATA_DIR, APP_DATA_DIR, SETTINGS_DIR


@st.cache_resource
def get_connection(db_path):
    """Get a cached database connection."""
    return sqlite3.connect(db_path, check_same_thread=False)


@st.cache_data
def get_available_databases():
    """Scan data folder for available Clear Aligner databases.
    
    Returns:
        dict: Mapping of project name to database path
    """
    db_files = list(DATA_DIR.glob("clear-aligner-*.sqlite"))
    db_files = [f for f in db_files if "-updated" not in f.name]
    
    projects = {}
    for db_file in sorted(db_files):
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.full_name, c.name
                FROM corpora c 
                WHERE c.side LIKE 'target%' 
                LIMIT 1
            """)
            row = cursor.fetchone()
            conn.close()
            
            if row:
                full_name, name = row
                project_name = full_name or name or db_file.stem
            else:
                project_name = db_file.stem
            
            projects[project_name] = str(db_file)
        except Exception:
            projects[db_file.stem] = str(db_file)
    
    return projects


@st.cache_data
def load_data(db_path):
    """Load alignment data with source and target words."""
    conn = get_connection(db_path)
    query = """
    WITH link_source_words AS (
        SELECT lsw.link_id, 
               GROUP_CONCAT(w.text, ' ') as source_text,
               MAX(w.required) as is_required,
               MIN(w.position_word) as min_src_pos
        FROM links__source_words lsw
        JOIN words_or_parts w ON lsw.word_id = w.id
        GROUP BY lsw.link_id
    ),
    link_target_words AS (
        SELECT ltw.link_id, 
               GROUP_CONCAT(w.text, ' ') as target_text,
               MIN(w.position_word) as min_tgt_pos
        FROM links__target_words ltw
        JOIN words_or_parts w ON ltw.word_id = w.id
        GROUP BY ltw.link_id
    )
    SELECT 
        l.id, 
        l.status, 
        l.origin,
        ls.source_text,
        ls.is_required,
        ls.min_src_pos,
        lt.target_text,
        lt.min_tgt_pos,
        w.position_book, 
        w.position_chapter, 
        w.position_verse
    FROM links l
    LEFT JOIN link_source_words ls ON l.id = ls.link_id
    LEFT JOIN link_target_words lt ON l.id = lt.link_id
    JOIN links__source_words lsw ON l.id = lsw.link_id
    JOIN words_or_parts w ON lsw.word_id = w.id
    GROUP BY l.id
    """
    df = pd.read_sql_query(query, conn)
    df['book_name'] = df['position_book'].map(BIBLE_BOOKS)
    df['testament'] = df['position_book'].apply(lambda x: "Old Testament" if x <= 39 else "New Testament")
    return df


@st.cache_data
def load_completion_data(db_path):
    """Load completion statistics per book."""
    conn = get_connection(db_path)
    query = """
    SELECT 
        w.position_book, 
        COUNT(w.id) as total_required,
        COUNT(DISTINCT CASE WHEN l.status IN ('approved', 'created') THEN w.id END) as completed
    FROM words_or_parts w
    LEFT JOIN links__source_words lsw ON w.id = lsw.word_id
    LEFT JOIN links l ON lsw.link_id = l.id
    WHERE w.id LIKE 'source%' AND w.required = 1
    GROUP BY w.position_book
    ORDER BY w.position_book
    """
    df = pd.read_sql_query(query, conn)
    df['book_name'] = df['position_book'].map(BIBLE_BOOKS)
    df['Completion %'] = (df['completed'] / df['total_required'] * 100).round(1)
    df['testament'] = df['position_book'].apply(lambda x: 'Old Testament' if x <= 39 else 'New Testament')
    return df


@st.cache_data
def load_app_data_index():
    """Load the app_data index.json."""
    index_path = APP_DATA_DIR / "index.json"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def load_settings():
    """Load settings from config.json."""
    config_path = SETTINGS_DIR / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"clearAlignerDataPath": "data", "autoSync": False, "lastSyncTime": None}


def save_settings(settings):
    """Save settings to config.json."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    config_path = SETTINGS_DIR / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)


def get_project_kpis(db_path):
    """Get KPIs from a SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM words_or_parts WHERE side = 'sources' AND language_id = 'grc'")
    source_nt = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM words_or_parts WHERE side = 'sources' AND language_id = 'heb'")
    source_ot = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM words_or_parts WHERE side LIKE 'target%'")
    target_words = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM links")
    links = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'source_nt': source_nt,
        'source_ot': source_ot,
        'target_words': target_words,
        'links': links
    }
