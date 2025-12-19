"""
ScriptureLens - Utilities Package
"""

from .constants import (
    APP_NAME,
    APP_VERSION,
    BIBLE_BOOKS,
    BOOK_NAME_TO_NUM,
    DATA_DIR,
    APP_DATA_DIR,
    SETTINGS_DIR,
    get_book_name,
    get_testament,
)

from .data_loader import (
    get_connection,
    get_available_databases,
    load_data,
    load_completion_data,
    load_app_data_index,
    load_settings,
    save_settings,
    get_project_kpis,
)

__all__ = [
    'APP_NAME',
    'APP_VERSION',
    'BIBLE_BOOKS',
    'BOOK_NAME_TO_NUM',
    'DATA_DIR',
    'APP_DATA_DIR',
    'SETTINGS_DIR',
    'get_book_name',
    'get_testament',
    'get_connection',
    'get_available_databases',
    'load_data',
    'load_completion_data',
    'load_app_data_index',
    'load_settings',
    'save_settings',
    'get_project_kpis',
]
