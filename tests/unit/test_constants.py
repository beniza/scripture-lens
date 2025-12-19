"""
Unit Tests for utils/constants.py
"""

import pytest
from utils.constants import (
    BIBLE_BOOKS,
    BOOK_NAME_TO_NUM,
    get_book_name,
    get_testament,
    APP_NAME,
    APP_VERSION,
)


class TestBibleBooks:
    """Tests for BIBLE_BOOKS dictionary."""
    
    def test_bible_books_has_66_books(self):
        """BIBLE_BOOKS should contain all 66 books."""
        assert len(BIBLE_BOOKS) == 66
    
    def test_bible_books_starts_with_genesis(self):
        """Book 1 should be Genesis."""
        assert BIBLE_BOOKS[1] == "Genesis"
    
    def test_bible_books_ends_with_revelation(self):
        """Book 66 should be Revelation."""
        assert BIBLE_BOOKS[66] == "Revelation"
    
    def test_ot_books_range(self):
        """Old Testament books are 1-39."""
        ot_books = {k: v for k, v in BIBLE_BOOKS.items() if k <= 39}
        assert len(ot_books) == 39
        assert BIBLE_BOOKS[39] == "Malachi"
    
    def test_nt_books_range(self):
        """New Testament books are 40-66."""
        nt_books = {k: v for k, v in BIBLE_BOOKS.items() if k >= 40}
        assert len(nt_books) == 27
        assert BIBLE_BOOKS[40] == "Matthew"
    
    def test_book_name_to_num_reverse_lookup(self):
        """BOOK_NAME_TO_NUM should be reverse of BIBLE_BOOKS."""
        assert BOOK_NAME_TO_NUM["Genesis"] == 1
        assert BOOK_NAME_TO_NUM["Revelation"] == 66
        assert BOOK_NAME_TO_NUM["Matthew"] == 40


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_get_book_name_valid(self):
        """get_book_name returns correct name."""
        assert get_book_name(1) == "Genesis"
        assert get_book_name(40) == "Matthew"
        assert get_book_name(66) == "Revelation"
    
    def test_get_book_name_invalid(self):
        """get_book_name returns fallback for invalid number."""
        assert get_book_name(0) == "Book 0"
        assert get_book_name(67) == "Book 67"
        assert get_book_name(-1) == "Book -1"
    
    def test_get_testament_ot(self):
        """get_testament returns 'Old Testament' for books 1-39."""
        assert get_testament(1) == "Old Testament"
        assert get_testament(39) == "Old Testament"
        assert get_testament(20) == "Old Testament"
    
    def test_get_testament_nt(self):
        """get_testament returns 'New Testament' for books 40-66."""
        assert get_testament(40) == "New Testament"
        assert get_testament(66) == "New Testament"
        assert get_testament(43) == "New Testament"


class TestAppInfo:
    """Tests for application info constants."""
    
    def test_app_name(self):
        """APP_NAME should be ScriptureLens."""
        assert APP_NAME == "ScriptureLens"
    
    def test_app_version_format(self):
        """APP_VERSION should be in semver format."""
        parts = APP_VERSION.split('.')
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)
