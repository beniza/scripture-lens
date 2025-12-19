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
def get_available_projects():
    """Scan app_data for projects and data/ for live databases.
    
    Returns:
        dict: Mapping of project_id to project info dict
    """
    projects = {}
    
    # 1. Load exported projects from app_data/index.json
    index_path = APP_DATA_DIR / "index.json"
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                for proj_id, proj_info in index_data.get('projects', {}).items():
                    projects[proj_id] = {
                        "id": proj_id,
                        "name": proj_info.get("name", proj_id),
                        "db_path": None,
                        "mode": "json",
                        "books": proj_info.get("books", [])
                    }
        except Exception as e:
            st.error(f"Error reading app_data index: {e}")

    # 2. Scan data folder for available SQLite databases
    if DATA_DIR.exists():
        db_files = list(DATA_DIR.glob("clear-aligner-*.sqlite"))
        db_files.extend(list(DATA_DIR.glob("demo-*.sqlite")))
        db_files = [f for f in db_files if "-updated" not in f.name]
        
        for db_file in sorted(db_files):
            try:
                # Try to map DB to existing project or create new one
                proj_id = db_file.stem
                # Extract actual project name from DB if possible
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                cursor.execute("SELECT full_name, name FROM corpora WHERE side LIKE 'target%' LIMIT 1")
                row = cursor.fetchone()
                conn.close()
                
                db_proj_name = row[0] or row[1] if row else db_file.stem
                
                # Check if this matches an exported project (simplified matching)
                matched = False
                for p_id, p_info in projects.items():
                    if p_id in db_file.name or db_file.stem in p_id:
                        p_info["db_path"] = str(db_file)
                        p_info["mode"] = "live"
                        matched = True
                        break
                
                if not matched:
                    projects[proj_id] = {
                        "id": proj_id,
                        "name": db_proj_name,
                        "db_path": str(db_file),
                        "mode": "live",
                        "books": [] # Will need to be fetched from DB
                    }
            except Exception:
                pass
    
    return projects


@st.cache_data
def load_data(project_id, db_path=None):
    """Load alignment data from SQLite if available, otherwise from JSON."""
    if db_path and Path(db_path).exists():
        return _load_data_sqlite(db_path)
    return _load_data_json(project_id)


def _load_data_sqlite(db_path):
    """Load from SQLite (existing logic)."""
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


def _load_data_json(project_id):
    """Load from JSON files in app_data (fallback)."""
    records = []
    project_dir = APP_DATA_DIR / "alignments" / project_id
    
    if not project_dir.exists():
        return pd.DataFrame()
        
    for json_file in project_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                book_num = data.get('book')
                book_name = data.get('bookName')
                
                for rec in data.get('records', []):
                    # We need to extract verse/chapter info from sourceIds
                    # Format: sources:BBBCCCVVVWWW
                    ref_id = rec.get('sourceIds', [None])[0]
                    chapter = 0
                    verse = 0
                    if ref_id and ':' in ref_id:
                        parts = ref_id.split(':')[-1]
                        if len(parts) >= 9:
                            chapter = int(parts[3:6])
                            verse = int(parts[6:9])
                    
                    records.append({
                        'id': rec.get('id'),
                        'status': rec.get('status'),
                        'origin': rec.get('origin'),
                        'source_text': ' '.join(rec.get('sourceText', [])),
                        'is_required': 1, # Default in exported data
                        'min_src_pos': 0, # Not strictly available in flat JSON without more work
                        'target_text': ' '.join(rec.get('targetText', [])),
                        'min_tgt_pos': 0,
                        'position_book': book_num,
                        'position_chapter': chapter,
                        'position_verse': verse,
                        'book_name': book_name,
                        'testament': "Old Testament" if book_num <= 39 else "New Testament"
                    })
        except Exception:
            continue
            
    return pd.DataFrame(records)


@st.cache_data
def load_completion_data(project_id, db_path=None):
    """Load completion statistics per book."""
    if db_path and Path(db_path).exists():
        return _load_completion_sqlite(db_path)
    return _load_completion_json(project_id)


def _load_completion_sqlite(db_path):
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


def _load_completion_json(project_id):
    """Fallback completion data from index.json stats."""
    index_path = APP_DATA_DIR / "index.json"
    if not index_path.exists():
        return pd.DataFrame()
        
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            proj = index_data.get('projects', {}).get(project_id, {})
            books = proj.get('books', [])
            
            records = []
            for b_info in books:
                records.append({
                    'position_book': b_info.get('book'),
                    'book_name': b_info.get('bookName'),
                    'total_required': 0, # Not easily available in basic index
                    'completed': b_info.get('alignmentCount', 0),
                    'Completion %': 100.0, # Placeholder for demo
                    'testament': "Old Testament" if b_info.get('book') <= 39 else "New Testament"
                })
            return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame()


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


def run_data_sync():
    """Run the data export script as a subprocess."""
    import subprocess
    import sys
    script_path = Path(__file__).parent.parent / "scripts" / "export_data.py"
    try:
        result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def get_project_kpis(project_id, db_path=None):
    """Get KPIs from SQLite if available, otherwise from JSON index."""
    if db_path and Path(db_path).exists():
        return _get_kpis_sqlite(db_path)
    return _get_kpis_json(project_id)


def _get_kpis_sqlite(db_path):
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


def _get_kpis_json(project_id):
    """Fallback KPIs from index.json."""
    index_path = APP_DATA_DIR / "index.json"
    if not index_path.exists():
        return {'source_nt': 0, 'source_ot': 0, 'target_words': 0, 'links': 0}
        
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            proj = index_data.get('projects', {}).get(project_id, {})
            stats = proj.get('stats', {})
            return {
                'source_nt': 8000, # Approximate for demo
                'source_ot': 0,
                'target_words': 15000,
                'links': stats.get('alignmentCount', 0)
            }
    except Exception:
        return {'source_nt': 0, 'source_ot': 0, 'target_words': 0, 'links': 0}

