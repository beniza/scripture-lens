"""
ScriptureLens Test Suite - Shared Fixtures
"""

import pytest
import sqlite3
import pandas as pd
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_bible_data():
    """Sample alignment data for testing."""
    return pd.DataFrame({
        'id': ['link1', 'link2', 'link3'],
        'status': ['approved', 'created', 'rejected'],
        'origin': ['manual', 'machine', 'manual'],
        'source_text': ['λόγος', 'θεός', 'ἀγάπη'],
        'is_required': [1, 1, 0],
        'min_src_pos': [1, 2, 3],
        'target_text': ['word', 'God', 'love'],
        'min_tgt_pos': [1, 2, 3],
        'position_book': [43, 43, 43],  # John
        'position_chapter': [1, 1, 1],
        'position_verse': [1, 1, 1],
        'book_name': ['John', 'John', 'John'],
        'testament': ['New Testament', 'New Testament', 'New Testament']
    })


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database with test data."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
        db_path = f.name
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE corpora (
            id TEXT PRIMARY KEY,
            name TEXT,
            full_name TEXT,
            side TEXT,
            language_id TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE words_or_parts (
            id TEXT PRIMARY KEY,
            text TEXT,
            lemma TEXT,
            gloss TEXT,
            normalized_text TEXT,
            side TEXT,
            language_id TEXT,
            required INTEGER,
            position_book INTEGER,
            position_chapter INTEGER,
            position_verse INTEGER,
            position_word INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE links (
            id TEXT PRIMARY KEY,
            status TEXT,
            origin TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE links__source_words (
            link_id TEXT,
            word_id TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE links__target_words (
            link_id TEXT,
            word_id TEXT
        )
    """)
    
    # Insert test data
    cursor.execute("""
        INSERT INTO corpora VALUES 
        ('corp1', 'TestProject', 'Test Project Full Name', 'targets', 'eng')
    """)
    
    cursor.execute("""
        INSERT INTO words_or_parts VALUES
        ('sources_1', 'λόγος', 'λόγος', 'word', 'λόγος', 'sources', 'grc', 1, 43, 1, 1, 1),
        ('sources_2', 'θεός', 'θεός', 'God', 'θεός', 'sources', 'grc', 1, 43, 1, 1, 2),
        ('targets_1', 'word', NULL, NULL, 'word', 'targets', 'eng', 0, 43, 1, 1, 1),
        ('targets_2', 'God', NULL, NULL, 'god', 'targets', 'eng', 0, 43, 1, 1, 2)
    """)
    
    cursor.execute("""
        INSERT INTO links VALUES
        ('link1', 'approved', 'manual'),
        ('link2', 'created', 'machine')
    """)
    
    cursor.execute("""
        INSERT INTO links__source_words VALUES
        ('link1', 'sources_1'),
        ('link2', 'sources_2')
    """)
    
    cursor.execute("""
        INSERT INTO links__target_words VALUES
        ('link1', 'targets_1'),
        ('link2', 'targets_2')
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup - handle Windows file locking
    try:
        os.unlink(db_path)
    except PermissionError:
        pass  # File may be locked by cached connection


@pytest.fixture
def mock_settings():
    """Mock settings dict."""
    return {
        "clearAlignerDataPath": "data",
        "autoSync": False,
        "lastSyncTime": None
    }
