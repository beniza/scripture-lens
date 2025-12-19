"""
ScriptureLens - Database Explorer Page
"""

import streamlit as st
import sqlite3
import pandas as pd
import os

from utils import DATA_DIR


def render(project_name, db_path):
    """Clean, elegant database explorer page."""
    
    # Build DB list with project names
    all_dbs = list(DATA_DIR.glob("clear-aligner-*.sqlite"))
    all_dbs.extend(list(DATA_DIR.glob("demo-*.sqlite")))
    all_dbs = sorted([f for f in all_dbs if "-updated" not in f.name])
    
    # Get project names for each database
    db_options = []
    db_map = {}  # display_name -> filename
    for db_file in all_dbs:
        try:
            temp_conn = sqlite3.connect(str(db_file))
            cursor = temp_conn.cursor()
            cursor.execute("SELECT full_name FROM corpora WHERE side LIKE 'target%' LIMIT 1")
            row = cursor.fetchone()
            display_name = row[0] if row else db_file.stem[:20]
            temp_conn.close()
        except:
            display_name = db_file.stem[:20]
        db_options.append(display_name)
        db_map[display_name] = db_file.name
    
    # Find current selection
    current_db_name = os.path.basename(db_path)
    current_display = next((k for k, v in db_map.items() if v == current_db_name), db_options[0] if db_options else "")
    current_idx = db_options.index(current_display) if current_display in db_options else 0
    
    # Compact header with DB selector inline
    col_header, col_db = st.columns([2, 3])
    with col_header:
        st.markdown("## 🗄️ Database Explorer")
    with col_db:
        selected_display = st.selectbox("", db_options, index=current_idx, label_visibility="collapsed")
    
    # Connect to selected database
    selected_db = db_map.get(selected_display, all_dbs[0].name if all_dbs else "")
    conn = sqlite3.connect(str(DATA_DIR / selected_db))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Tabs for clean navigation
    tab_query, tab_browse, tab_schema = st.tabs(["💻 SQL Query", "📋 Browse Tables", "📊 Schema"])
    
    # SQL Query Tab
    with tab_query:
        query = st.text_area(
            "Enter SQL",
            value="SELECT * FROM links LIMIT 20",
            height=80,
            label_visibility="collapsed",
            placeholder="SELECT * FROM table_name LIMIT 100"
        )
        
        if st.button("▶️ Execute", type="primary"):
            try:
                df = pd.read_sql_query(query, conn)
                st.caption(f"✓ {len(df):,} rows returned")
                st.dataframe(df, use_container_width=True, height=450)
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Browse Tables Tab
    with tab_browse:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            table = st.selectbox("Table", tables, label_visibility="collapsed")
        with col2:
            limit = st.selectbox("Rows", [25, 50, 100, 500], index=0, label_visibility="collapsed")
        with col3:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total = cursor.fetchone()[0]
            st.caption(f"{total:,} total")
        
        df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT {limit}", conn)
        st.dataframe(df, use_container_width=True, height=450)
    
    # Schema Tab
    with tab_schema:
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            rows = cursor.fetchone()[0]
            cursor.execute(f"PRAGMA table_info({tbl})")
            cols = cursor.fetchall()
            
            with st.expander(f"**{tbl}** · {rows:,} rows · {len(cols)} cols"):
                schema_df = pd.DataFrame(cols, columns=['#', 'Column', 'Type', 'NotNull', 'Default', 'PK'])
                st.dataframe(schema_df[['Column', 'Type', 'PK']], use_container_width=True, hide_index=True, height=min(200, len(cols)*35+40))
    
    conn.close()
