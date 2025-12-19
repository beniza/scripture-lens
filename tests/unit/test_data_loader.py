"""
Unit Tests for utils/data_loader.py
"""

import pytest
import sqlite3
import pandas as pd
from unittest.mock import patch, MagicMock


class TestGetProjectKpis:
    """Tests for get_project_kpis function."""
    
    def test_get_project_kpis_returns_dict(self, temp_db):
        """get_project_kpis should return a dict with expected keys."""
        from utils.data_loader import get_project_kpis
        
        result = get_project_kpis(temp_db)
        
        assert isinstance(result, dict)
        assert 'source_nt' in result
        assert 'source_ot' in result
        assert 'target_words' in result
        assert 'links' in result
    
    def test_get_project_kpis_counts(self, temp_db):
        """get_project_kpis should return correct counts."""
        from utils.data_loader import get_project_kpis
        
        result = get_project_kpis(temp_db)
        
        # Based on our test data: 2 Greek sources, 0 Hebrew, 2 targets, 2 links
        assert result['source_nt'] == 2  # grc sources
        assert result['source_ot'] == 0  # heb sources
        assert result['target_words'] == 2
        assert result['links'] == 2


class TestLoadSettings:
    """Tests for load_settings and save_settings functions."""
    
    def test_load_settings_default(self, tmp_path):
        """load_settings returns defaults when no config exists."""
        from utils.data_loader import load_settings
        
        with patch('utils.data_loader.SETTINGS_DIR', tmp_path):
            result = load_settings()
        
        assert result['clearAlignerDataPath'] == 'data'
        assert result['autoSync'] == False
        assert result['lastSyncTime'] is None
    
    def test_save_and_load_settings(self, tmp_path):
        """save_settings persists and load_settings retrieves."""
        from utils.data_loader import load_settings, save_settings
        
        with patch('utils.data_loader.SETTINGS_DIR', tmp_path):
            test_settings = {
                'clearAlignerDataPath': 'custom/path',
                'autoSync': True,
                'lastSyncTime': '2024-01-01T00:00:00'
            }
            save_settings(test_settings)
            result = load_settings()
        
        assert result['clearAlignerDataPath'] == 'custom/path'
        assert result['autoSync'] == True
        assert result['lastSyncTime'] == '2024-01-01T00:00:00'


class TestLoadAppDataIndex:
    """Tests for load_app_data_index function."""
    
    def test_load_app_data_index_missing(self, tmp_path):
        """Returns None when index.json doesn't exist."""
        from utils.data_loader import load_app_data_index
        
        with patch('utils.data_loader.APP_DATA_DIR', tmp_path):
            # Clear cache to avoid stale data
            load_app_data_index.clear()
            result = load_app_data_index()
        
        assert result is None
    
    def test_load_app_data_index_exists(self, tmp_path):
        """Returns parsed JSON when index.json exists."""
        import json
        from utils.data_loader import load_app_data_index
        
        # Create test index.json
        index_data = {
            'projects': {
                'test': {'name': 'Test Project', 'language': 'eng'}
            }
        }
        index_path = tmp_path / 'index.json'
        index_path.write_text(json.dumps(index_data))
        
        with patch('utils.data_loader.APP_DATA_DIR', tmp_path):
            load_app_data_index.clear()
            result = load_app_data_index()
        
        assert result is not None
        assert 'projects' in result
        assert 'test' in result['projects']


class TestGetAvailableDatabases:
    """Tests for get_available_databases function."""
    
    def test_get_available_databases_empty(self, tmp_path):
        """Returns empty dict when no databases exist."""
        from utils.data_loader import get_available_databases
        
        with patch('utils.data_loader.DATA_DIR', tmp_path):
            get_available_databases.clear()
            result = get_available_databases()
        
        assert result == {}
    
    def test_get_available_databases_finds_dbs(self, tmp_path, temp_db):
        """Returns dict with project names when databases exist."""
        import shutil
        from utils.data_loader import get_available_databases
        
        # Copy temp_db to tmp_path with correct naming
        dest = tmp_path / "clear-aligner-test-uuid.sqlite"
        shutil.copy(temp_db, dest)
        
        with patch('utils.data_loader.DATA_DIR', tmp_path):
            get_available_databases.clear()
            result = get_available_databases()
        
        assert len(result) == 1
        assert "Test Project Full Name" in result


class TestLoadData:
    """Tests for load_data function."""
    
    def test_load_data_returns_dataframe(self, temp_db):
        """load_data should return a DataFrame."""
        from utils.data_loader import load_data
        
        load_data.clear()
        result = load_data(temp_db)
        
        assert isinstance(result, pd.DataFrame)
    
    def test_load_data_has_expected_columns(self, temp_db):
        """load_data DataFrame should have expected columns."""
        from utils.data_loader import load_data
        
        load_data.clear()
        result = load_data(temp_db)
        
        expected_columns = ['id', 'status', 'source_text', 'target_text', 
                           'position_book', 'book_name', 'testament']
        for col in expected_columns:
            assert col in result.columns
    
    def test_load_data_book_name_mapped(self, temp_db):
        """load_data should map book numbers to names."""
        from utils.data_loader import load_data
        
        load_data.clear()
        result = load_data(temp_db)
        
        if not result.empty:
            assert result['book_name'].iloc[0] == 'John'  # Book 43


class TestLoadCompletionData:
    """Tests for load_completion_data function."""
    
    def test_load_completion_data_returns_dataframe(self, temp_db):
        """load_completion_data should return a DataFrame."""
        from utils.data_loader import load_completion_data
        
        load_completion_data.clear()
        result = load_completion_data(temp_db)
        
        assert isinstance(result, pd.DataFrame)
    
    def test_load_completion_data_has_completion_pct(self, temp_db):
        """load_completion_data should have Completion % column."""
        from utils.data_loader import load_completion_data
        
        load_completion_data.clear()
        result = load_completion_data(temp_db)
        
        assert 'Completion %' in result.columns
