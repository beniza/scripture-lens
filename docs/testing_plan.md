# ScriptureLens Testing Plan

## Overview

Comprehensive test suite covering unit tests, integration tests, and end-to-end tests for the ScriptureLens application.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures (test DB, mock data)
├── unit/
│   ├── __init__.py
│   ├── test_constants.py    # BIBLE_BOOKS, paths
│   ├── test_data_loader.py  # SQL queries, caching
│   └── test_helpers.py      # Utility functions
├── integration/
│   ├── __init__.py
│   ├── test_pages.py        # Page render without errors
│   └── test_export.py       # Export script functionality
└── e2e/
    ├── __init__.py
    └── test_app_flow.py     # Full app navigation (Playwright/Selenium)
```

---

## 1. Unit Tests

### `test_constants.py`
| Test                        | Description                        |
| --------------------------- | ---------------------------------- |
| `test_bible_books_complete` | All 66 books present               |
| `test_bible_books_ot_range` | Books 1-39 are OT                  |
| `test_bible_books_nt_range` | Books 40-66 are NT                 |
| `test_get_book_name`        | Returns correct name for number    |
| `test_get_testament`        | Returns correct testament          |
| `test_paths_exist`          | DATA_DIR, APP_DATA_DIR paths valid |

### `test_data_loader.py`
| Test                                 | Description                    |
| ------------------------------------ | ------------------------------ |
| `test_get_available_databases`       | Returns dict of project → path |
| `test_get_available_databases_empty` | Returns empty dict if no DBs   |
| `test_load_data_columns`             | DataFrame has expected columns |
| `test_load_data_book_names`          | Book names mapped correctly    |
| `test_load_data_testament`           | Testament column populated     |
| `test_load_completion_data`          | Returns completion percentages |
| `test_load_app_data_index`           | Loads JSON index correctly     |
| `test_load_settings`                 | Loads config.json              |
| `test_save_settings`                 | Saves and persists settings    |
| `test_get_project_kpis`              | Returns KPI dict with counts   |

---

## 2. Integration Tests

### `test_pages.py`
| Test                      | Description                |
| ------------------------- | -------------------------- |
| `test_drill_down_render`  | Page renders without error |
| `test_completion_render`  | Page renders without error |
| `test_interlinear_render` | Page renders without error |
| `test_concordance_render` | Page renders without error |
| `test_comparison_render`  | Page renders without error |
| `test_settings_render`    | Page renders without error |
| `test_db_explorer_render` | Page renders without error |

### `test_export.py`
| Test                                  | Description                  |
| ------------------------------------- | ---------------------------- |
| `test_export_source_text`             | Exports Greek/Hebrew sources |
| `test_export_target_text`             | Exports target language      |
| `test_export_alignments`              | Exports alignment links      |
| `test_export_creates_index`           | Creates index.json           |
| `test_export_alignment_count_matches` | SQLite = JSON counts         |

---

## 3. E2E Tests (Browser)

### `test_app_flow.py`
| Test                          | Description                    |
| ----------------------------- | ------------------------------ |
| `test_app_loads`              | App loads without errors       |
| `test_project_selection`      | Can select different projects  |
| `test_navigation`             | All pages accessible via nav   |
| `test_drill_down_filters`     | Filters update data correctly  |
| `test_concordance_flow`       | Lemma → Rendering → Verse flow |
| `test_interlinear_navigation` | Book/chapter navigation works  |
| `test_db_explorer_query`      | SQL query executes             |
| `test_settings_sync`          | Sync button triggers export    |

---

## Test Fixtures (`conftest.py`)

```python
@pytest.fixture
def test_db_path():
    """Path to test SQLite database."""
    return "tests/fixtures/test_alignment.sqlite"

@pytest.fixture
def sample_df():
    """Sample alignment DataFrame for testing."""
    return pd.DataFrame({...})

@pytest.fixture
def mock_settings():
    """Mock settings dict."""
    return {"clearAlignerDataPath": "data", "autoSync": False}
```

---

## Test Data Requirements

1. **Fixture Database** (`tests/fixtures/test_alignment.sqlite`)
   - Small subset of real data (1 book, ~100 links)
   - Covers all table structures

2. **Mock JSON** (`tests/fixtures/`)
   - `index.json` - Sample index
   - `sources/greek/40_matthew.json` - Sample source
   - `targets/test/40_matthew.json` - Sample target

---

## Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# With coverage
uv run pytest tests/ --cov=. --cov-report=html

# E2E tests (requires browser)
uv run pytest tests/e2e/ -v --headed
```

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest tests/ -v --cov
```

---

## Priority Order

1. **High** - `test_data_loader.py` (core functionality)
2. **High** - `test_export.py` (data integrity)
3. **Medium** - `test_pages.py` (page rendering)
4. **Medium** - `test_constants.py` (quick to write)
5. **Low** - `test_app_flow.py` (E2E, more setup)

---

## Next Steps

1. Add pytest to dependencies
2. Create `tests/` folder structure
3. Create fixture database
4. Implement unit tests first
5. Add integration tests
6. Add E2E tests (optional)
