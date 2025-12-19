"""
ScriptureLens - Bible Alignment Viewer
A Streamlit application for viewing and analyzing Clear Aligner data.
"""

import streamlit as st

from utils import (
    get_available_databases,
    load_data,
)
from pages import (
    scripture,
    drill_down,
    completion,
    interlinear,
    interlinear_v2,
    concordance,
    comparison,
    settings,
    db_explorer,
)

# Page Configuration
st.set_page_config(
    page_title="ScriptureLens",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def main():
    """Main application entry point."""
    
    # Load available projects
    projects = get_available_databases()
    
    if not projects:
        st.error("No database files found in the 'data' folder.")
        st.info("Place Clear Aligner `.sqlite` files in the `data/` folder.")
        return
    
    # Header row: Title + Project selector + Refresh
    col_title, col_project, col_refresh = st.columns([2, 3, 0.5])
    
    with col_title:
        st.markdown("### 📖 ScriptureLens")
    
    with col_project:
        project_names = sorted(list(projects.keys()))
        selected_project = st.selectbox(
            "Project",
            project_names,
            label_visibility="collapsed"
        )
    
    with col_refresh:
        if st.button("🔄", help="Refresh database list"):
            get_available_databases.clear()
            st.rerun()
    
    db_path = projects[selected_project]

    # Load main data
    with st.spinner(f"Loading {selected_project}..."):
        df = load_data(db_path)

    # Navigation tabs
    tabs = st.tabs([
        "📜 Scripture",
        "📖 Interlinear",
        "📚 Concordance", 
        "🔍 Drill-down",
        "📊 Completion",
        "🔄 Comparison",
        "🗄️ Database",
        "⚙️ Settings"
    ])
    
    with tabs[0]:
        scripture.render(selected_project, db_path)
    
    with tabs[1]:
        interlinear_v2.render(selected_project, db_path)
    
    with tabs[2]:
        concordance.render(selected_project, db_path)
    
    with tabs[3]:
        drill_down.render(df, selected_project, db_path)
    
    with tabs[4]:
        completion.render(df, selected_project, db_path)
    
    with tabs[5]:
        comparison.render(selected_project, db_path)
    
    with tabs[6]:
        db_explorer.render(selected_project, db_path)
    
    with tabs[7]:
        settings.render(selected_project, db_path)


if __name__ == "__main__":
    main()
