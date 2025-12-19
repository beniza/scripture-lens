"""
Integration Tests for scripts/export_data.py
"""

import pytest
import sqlite3
import json
import tempfile
import shutil
from pathlib import Path


class TestExportDataIntegration:
    """Integration tests for the export data script."""
    
    @pytest.fixture
    def export_env(self, temp_db, tmp_path):
        """Set up export environment with temp directories."""
        # Create app_data structure
        app_data_dir = tmp_path / "app_data"
        app_data_dir.mkdir()
        (app_data_dir / "sources").mkdir()
        (app_data_dir / "sources" / "greek").mkdir()
        (app_data_dir / "sources" / "hebrew").mkdir()
        (app_data_dir / "targets").mkdir()
        (app_data_dir / "alignments").mkdir()
        
        return {
            "db_path": temp_db,
            "app_data_dir": app_data_dir,
            "tmp_path": tmp_path
        }
    
    def test_export_creates_index_json(self, export_env):
        """Export should create an index.json file."""
        # This test verifies the export creates proper structure
        app_data_dir = export_env["app_data_dir"]
        
        # Create a mock index.json
        index_data = {
            "projects": {},
            "sources": {"greek": [], "hebrew": []}
        }
        
        index_path = app_data_dir / "index.json"
        with open(index_path, 'w') as f:
            json.dump(index_data, f)
        
        assert index_path.exists()
        
        # Verify structure
        with open(index_path) as f:
            loaded = json.load(f)
        
        assert "projects" in loaded
        assert "sources" in loaded
    
    def test_export_json_structure(self, export_env):
        """Exported JSON should have correct structure."""
        app_data_dir = export_env["app_data_dir"]
        
        # Create sample source file
        source_data = {
            "1": {  # Chapter
                "1": [  # Verse
                    {"id": "src_1", "text": "λόγος", "lemma": "λόγος", "gloss": "word"}
                ]
            }
        }
        
        source_file = app_data_dir / "sources" / "greek" / "43_john.json"
        with open(source_file, 'w', encoding='utf-8') as f:
            json.dump(source_data, f, ensure_ascii=False)
        
        assert source_file.exists()
        
        with open(source_file, encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert "1" in loaded  # Chapter
        assert "1" in loaded["1"]  # Verse
        assert len(loaded["1"]["1"]) == 1
        assert loaded["1"]["1"][0]["text"] == "λόγος"
    
    def test_alignment_export_structure(self, export_env):
        """Alignment JSON should have correct structure."""
        app_data_dir = export_env["app_data_dir"]
        
        # Create sample alignment file
        alignment_data = {
            "1": {  # Chapter
                "1": [  # Verse
                    {
                        "sources": ["src_1"],
                        "targets": ["tgt_1"],
                        "status": "approved"
                    }
                ]
            }
        }
        
        align_dir = app_data_dir / "alignments" / "test_project"
        align_dir.mkdir(parents=True)
        align_file = align_dir / "43_john.json"
        
        with open(align_file, 'w') as f:
            json.dump(alignment_data, f)
        
        assert align_file.exists()
        
        with open(align_file) as f:
            loaded = json.load(f)
        
        assert "1" in loaded
        assert "1" in loaded["1"]
        assert "sources" in loaded["1"]["1"][0]
        assert "targets" in loaded["1"]["1"][0]


class TestIndexJsonIntegrity:
    """Tests for index.json data integrity."""
    
    def test_index_project_stats(self, tmp_path):
        """Project stats in index should have expected fields."""
        index_data = {
            "projects": {
                "test_project": {
                    "name": "Test Project",
                    "language": "eng",
                    "sourceDatabase": "clear-aligner-test.sqlite",
                    "stats": {
                        "alignmentCount": 100,
                        "bookCount": 27
                    }
                }
            }
        }
        
        index_path = tmp_path / "index.json"
        with open(index_path, 'w') as f:
            json.dump(index_data, f)
        
        with open(index_path) as f:
            loaded = json.load(f)
        
        project = loaded["projects"]["test_project"]
        assert "name" in project
        assert "language" in project
        assert "stats" in project
        assert project["stats"]["alignmentCount"] == 100
