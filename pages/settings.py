"""
ScriptureLens - Settings Page (Redesigned)
Compact, organized settings with appearance customization
"""

import streamlit as st
import subprocess
import datetime
from pathlib import Path

from utils import load_settings, save_settings, load_app_data_index, APP_DATA_DIR

# Google Fonts options
FONT_OPTIONS = {
    "System Default": "",
    "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap",
    "Noto Sans": "https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&display=swap",
    "Gentium Plus": "https://fonts.googleapis.com/css2?family=Gentium+Plus:wght@400;700&display=swap",
    "SBL Greek": "",
    "Ezra SIL": "",
}

FONT_SIZE_OPTIONS = ["Small", "Medium", "Large"]
THEME_OPTIONS = ["Light", "Dark", "Auto"]

def run_data_sync():
    """Run the export_data.py script to sync data from SQLite to JSON."""
    result = subprocess.run(
        ["uv", "run", "python", "scripts/export_data.py"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    settings = load_settings()
    settings["lastSyncTime"] = datetime.datetime.now().isoformat()
    save_settings(settings)
    load_app_data_index.clear()
    return result.returncode == 0, result.stdout, result.stderr


def render(project_name, db_path):
    """Compact, tabbed settings page."""
    settings = load_settings()
    
    # Tabs for organization
    tab_appearance, tab_data, tab_ai = st.tabs(["🎨 Appearance", "📂 Data", "🤖 AI"])
    
    # === APPEARANCE TAB ===
    with tab_appearance:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Typography")
            
            # Font family
            current_font = settings.get("fontFamily", "System Default")
            font = st.selectbox("Font", list(FONT_OPTIONS.keys()), 
                               index=list(FONT_OPTIONS.keys()).index(current_font) if current_font in FONT_OPTIONS else 0,
                               key="font_family")
            if font != current_font:
                settings["fontFamily"] = font
                save_settings(settings)
            
            # Font size
            current_size = settings.get("fontSize", "Medium")
            size = st.select_slider("Size", FONT_SIZE_OPTIONS, value=current_size, key="font_size")
            if size != current_size:
                settings["fontSize"] = size
                save_settings(settings)
            
            # Custom font URL
            with st.expander("Custom Web Font"):
                custom_url = settings.get("customFontUrl", "")
                new_url = st.text_input("Font URL (Google Fonts)", value=custom_url, 
                                       placeholder="https://fonts.googleapis.com/css2?family=...")
                if new_url != custom_url:
                    settings["customFontUrl"] = new_url
                    save_settings(settings)
        
        with col2:
            st.markdown("##### Colors")
            
            # Primary color
            current_primary = settings.get("primaryColor", "#1976d2")
            primary = st.color_picker("Primary", current_primary, key="primary_color")
            if primary != current_primary:
                settings["primaryColor"] = primary
                save_settings(settings)
            
            # Accent color
            current_accent = settings.get("accentColor", "#2e7d32")
            accent = st.color_picker("Accent", current_accent, key="accent_color")
            if accent != current_accent:
                settings["accentColor"] = accent
                save_settings(settings)
            
            # Theme
            current_theme = settings.get("theme", "Light")
            theme = st.radio("Theme", THEME_OPTIONS, 
                            index=THEME_OPTIONS.index(current_theme) if current_theme in THEME_OPTIONS else 0,
                            horizontal=True, key="theme")
            if theme != current_theme:
                settings["theme"] = theme
                save_settings(settings)
        
        # Preview
        st.divider()
        st.markdown("##### Preview")
        preview_html = f"""
        <div style="padding:16px; background:#f5f5f5; border-radius:8px; font-family: {font if font != 'System Default' else 'inherit'};">
            <span style="color:{primary}; font-weight:bold;">Primary Text</span> • 
            <span style="color:{accent};">Accent Text</span> • 
            <span style="color:#333;">Regular Text</span>
        </div>
        """
        st.markdown(preview_html, unsafe_allow_html=True)
    
    # === DATA TAB ===
    with tab_data:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("##### Data Path")
            current_path = settings.get("clearAlignerDataPath", "data")
            new_path = st.text_input("SQLite folder", value=current_path, label_visibility="collapsed")
            
            if new_path != current_path:
                settings["clearAlignerDataPath"] = new_path
                save_settings(settings)
            
            # Status
            data_path = Path(__file__).parent.parent / new_path
            if data_path.exists():
                db_files = [f for f in data_path.glob("clear-aligner-*.sqlite") if "-updated" not in f.name]
                st.caption(f"📁 {len(db_files)} databases found")
            else:
                st.caption("⚠️ Path not found")
        
        with col2:
            st.markdown("##### Sync")
            last_sync = settings.get("lastSyncTime", "Never")
            st.caption(f"Last: {last_sync[:16] if last_sync != 'Never' else 'Never'}")
            
            if st.button("🔄 Sync Now", type="primary", use_container_width=True):
                with st.spinner("Syncing..."):
                    success, _, stderr = run_data_sync()
                    if success:
                        st.success("✓")
                        st.rerun()
                    else:
                        st.error("Failed")
        
        # Projects
        st.divider()
        st.markdown("##### Projects")
        index = load_app_data_index()
        if index:
            projects = index.get('projects', {})
            for proj_id, proj in projects.items():
                stats = proj.get('stats', {})
                st.caption(f"• {proj.get('name', proj_id)}: {stats.get('alignmentCount', 0):,} alignments")
        else:
            st.caption("No data. Run sync.")
    
    # === AI TAB ===
    with tab_ai:
        render_ai_settings(settings)


def render_ai_settings(settings):
    """Compact AI/LLM settings."""
    from utils.llm import (
        LLMProvider, get_all_providers_status, get_provider_display_name,
        get_provider_help_url, test_connection, fetch_available_models, DEFAULT_MODELS
    )
    
    providers = get_all_providers_status()
    configured = [p for p, c in providers.items() if c.is_configured]
    
    # Default provider
    if configured:
        col1, col2 = st.columns([2, 1])
        with col1:
            current_default = settings.get("defaultLLMProvider", configured[0].value)
            options = [get_provider_display_name(p) for p in configured]
            values = [p.value for p in configured]
            idx = values.index(current_default) if current_default in values else 0
            
            selected = st.selectbox("Default Provider", options, index=idx)
            new_val = values[options.index(selected)]
            if new_val != current_default:
                settings["defaultLLMProvider"] = new_val
                save_settings(settings)
    else:
        st.info("No AI providers configured. Add API keys to .env file.")
    
    st.divider()
    
    # Provider list (compact)
    for provider, config in providers.items():
        status = "✅" if config.is_configured else "⚠️"
        with st.expander(f"{status} {get_provider_display_name(provider)}", expanded=False):
            if config.is_configured:
                col1, col2 = st.columns([3, 1])
                with col1:
                    success, models = fetch_available_models(provider)
                    if models:
                        saved = settings.get(f"llm_{provider.value}_model", DEFAULT_MODELS.get(provider, ""))
                        idx = models.index(saved) if saved in models else 0
                        model = st.selectbox("Model", models, index=idx, key=f"m_{provider.value}")
                        if model != saved:
                            settings[f"llm_{provider.value}_model"] = model
                            save_settings(settings)
                with col2:
                    if st.button("Test", key=f"t_{provider.value}"):
                        model = settings.get(f"llm_{provider.value}_model", DEFAULT_MODELS.get(provider))
                        ok, msg = test_connection(provider, model)
                        st.success("✓") if ok else st.error("✗")
            else:
                url = get_provider_help_url(provider)
                if url:
                    st.markdown(f"[Get API Key →]({url})")
                st.caption("Add to .env file")
