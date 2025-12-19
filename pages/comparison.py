"""
ScriptureLens - Data Comparison Page
"""

import streamlit as st
import pandas as pd

from utils import (
    APP_DATA_DIR,
    DATA_DIR,
    load_app_data_index,
    get_project_kpis,
)


def render(project_name, db_path):
    """Simple KPI comparison page showing Source Words (NT/OT), Target Words, Links for each project."""
    st.header("📊 Project KPI Comparison")
    st.markdown("Compare SQLite vs Exported JSON data for each project")
    
    # Check if app_data exists
    if not APP_DATA_DIR.exists():
        st.warning("⚠️ `app_data/` folder not found. Run `export_data.py` first.")
        st.code("uv run python export_data.py", language="bash")
        return
    
    # Load app_data index
    index = load_app_data_index()
    if not index:
        st.warning("⚠️ `app_data/index.json` not found. Run `export_data.py` first.")
        return
    
    # Build comparison table for all projects
    comparison_data = []
    
    for proj_id, proj in index.get('projects', {}).items():
        source_db = proj.get('sourceDatabase', '')
        db_file = DATA_DIR / source_db
        
        if db_file.exists():
            sqlite_kpis = get_project_kpis(str(db_file))
        else:
            sqlite_kpis = {'source_nt': 0, 'source_ot': 0, 'target_words': 0, 'links': 0}
        
        # Get exported stats
        json_links = proj.get('stats', {}).get('alignmentCount', 0)
        
        comparison_data.append({
            'Project': proj.get('name', proj_id),
            'Language': proj.get('language', ''),
            'Source NT': f"{sqlite_kpis['source_nt']:,}",
            'Source OT': f"{sqlite_kpis['source_ot']:,}",
            'Target Words': f"{sqlite_kpis['target_words']:,}",
            'SQLite Links': f"{sqlite_kpis['links']:,}",
            'JSON Links': f"{json_links:,}",
            'Match': '✅' if sqlite_kpis['links'] == json_links else '❌'
        })
    
    if comparison_data:
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
    else:
        st.info("No projects found in app_data/index.json")
