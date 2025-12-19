"""
ScriptureLens - Main Entry Point
Streamlit dashboard for visualizing Bible alignment data.
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Set page config FIRST
st.set_page_config(
    page_title="ScriptureLens Dashboard",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils import get_available_projects, load_data, load_completion_data
from views import scripture, drill_down, completion, comparison, interlinear_v2, db_explorer, concordance, settings

def main():
    """Main application entry point."""
    
    # Load available projects (JSON-first)
    projects = get_available_projects()
    
    if not projects:
        st.error("No project data found in 'app_data' or 'data' folder.")
        st.info("Ensure alignment data is exported to `app_data/` or SQLite files are in `data/`.")
        return
    
    # Header row: Title + Project selector + Refresh
    col_title, col_project, col_refresh = st.columns([2, 3, 0.5])
    
    with col_title:
        st.markdown("### 📖 ScriptureLens")
    
    with col_project:
        project_display_names = {p['name']: p_id for p_id, p in projects.items()}
        selected_display = st.selectbox(
            "Project",
            sorted(list(project_display_names.keys())),
            label_visibility="collapsed"
        )
        selected_id = project_display_names[selected_display]
        project_info = projects[selected_id]
        db_path = project_info.get('db_path')
        is_live = project_info.get('mode') == 'live'
    
    with col_refresh:
        if st.button("🔄", help="Refresh data"):
            get_available_projects.clear()
            st.rerun()
    
    # Load main data
    with st.spinner(f"Loading {selected_display}..."):
        df = load_data(selected_id, db_path)

    # Define tabs - some are only visible in "Live" mode
    if is_live:
        tab_list = [
            "📜 Scripture",
            "📖 Interlinear",
            "📚 Concordance", 
            "🔍 Drill-down",
            "📊 Completion",
            "🔄 Comparison",
            "🗄️ Database",
            "⚙️ Settings"
        ]
    else:
        tab_list = [
            "📜 Scripture",
            "📖 Interlinear",
            "📊 Completion",
            "⚙️ Settings"
        ]

    tabs = st.tabs(tab_list)
    
    if is_live:
        with tabs[0]:
            scripture.render(selected_id, db_path)
        with tabs[1]:
            interlinear_v2.render(selected_id, db_path)
        with tabs[2]:
            concordance.render(selected_id, db_path)
        with tabs[3]:
            drill_down.render(df, selected_id, db_path)
        with tabs[4]:
            completion.render(df, selected_id, db_path)
        with tabs[5]:
            comparison.render(selected_id, db_path)
        with tabs[6]:
            db_explorer.render(selected_id, db_path)
        with tabs[7]:
            settings.render(selected_id, db_path)
    else:
        with tabs[0]:
            scripture.render(selected_id, db_path)
        with tabs[1]:
            interlinear_v2.render(selected_id, db_path)
        with tabs[2]:
            completion.render(df, selected_id, db_path)
        with tabs[3]:
            settings.render(selected_id, db_path)


if __name__ == "__main__":
    main()
