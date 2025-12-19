"""
Data Preparation Script for Bible Alignment App

Exports data from ALL ClearAligner SQLite databases to JSON format.
Creates the app_data folder structure with:
- Source text (Greek/Hebrew) per book
- Target text per book (per project)
- Alignment data per book (per project)
- UBS dictionaries (downloaded)
- Index with source database references
"""

import json
import sqlite3
import os
import sys
import glob
from collections import defaultdict
from pathlib import Path
import urllib.request

# Fix console encoding for non-ASCII characters
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
APP_DATA_DIR = Path(__file__).parent.parent / "app_data"

# Bible book info
BIBLE_BOOKS = {
    # OT
    1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
    6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
    11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles",
    15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms",
    20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
    24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
    28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah",
    33: "Micah", 34: "Nahum", 35: "Habakkuk", 36: "Zephaniah", 37: "Haggai",
    38: "Zechariah", 39: "Malachi",
    # NT
    40: "Matthew", 41: "Mark", 42: "Luke", 43: "John", 44: "Acts",
    45: "Romans", 46: "1 Corinthians", 47: "2 Corinthians", 48: "Galatians",
    49: "Ephesians", 50: "Philippians", 51: "Colossians", 52: "1 Thessalonians",
    53: "2 Thessalonians", 54: "1 Timothy", 55: "2 Timothy", 56: "Titus",
    57: "Philemon", 58: "Hebrews", 59: "James", 60: "1 Peter", 61: "2 Peter",
    62: "1 John", 63: "2 John", 64: "3 John", 65: "Jude", 66: "Revelation"
}

# UBS Dictionary URLs
UBS_DICTIONARIES = {
    "UBSGreekNTDic-v1.1-en.json": "https://raw.githubusercontent.com/ubsicap/ubs-open-license/main/dictionaries/greek/JSON/UBSGreekNTDic-v1.1-en.JSON",
    "UBSHebrewDic-v0.9.1-en.json": "https://raw.githubusercontent.com/ubsicap/ubs-open-license/main/dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.1-en.JSON",
}


def get_project_info(conn, db_filename):
    """Extract project info from database corpora table."""
    cursor = conn.cursor()
    
    # Get target corpus info
    cursor.execute("""
        SELECT id, name, full_name, language_id 
        FROM corpora 
        WHERE side LIKE 'target%'
        LIMIT 1
    """)
    row = cursor.fetchone()
    
    if row:
        corpus_id, name, full_name, lang = row
        # Create a slug from the name
        project_id = name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "")
        return {
            "projectId": project_id,
            "name": full_name or name,
            "language": lang,
            "corpusId": corpus_id
        }
    
    # Fallback: use database filename
    db_id = db_filename.replace("clear-aligner-", "").replace(".sqlite", "")
    return {
        "projectId": f"project-{db_id[:8]}",
        "name": f"Project {db_id[:8]}",
        "language": "unknown",
        "corpusId": None
    }


def create_project_folders(project_id):
    """Create folders for a specific project."""
    folders = [
        APP_DATA_DIR / "targets" / project_id,
        APP_DATA_DIR / "alignments" / project_id,
    ]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)


def export_source_text(conn, sources_exported):
    """Export Greek/Hebrew source text to JSON files (shared across projects)."""
    if sources_exported:
        print("  Source text already exported, skipping...")
        return True
    
    print("\n=== Exporting source text ===")
    
    # Create source folders
    (APP_DATA_DIR / "sources" / "greek").mkdir(parents=True, exist_ok=True)
    (APP_DATA_DIR / "sources" / "hebrew").mkdir(parents=True, exist_ok=True)
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT position_book, position_chapter, position_verse, position_word,
               id, text, lemma, gloss, language_id, required, after
        FROM words_or_parts
        WHERE side = 'sources'
          AND ((position_book = 43 AND position_chapter IN (1,2,3)) OR
               (position_book = 45 AND position_chapter IN (1,2,3,4,5,6,7,8)) OR
               (position_book = 40 AND position_chapter IN (5,6,7)))
        ORDER BY position_book, position_chapter, position_verse, position_word
    """)
    
    books = defaultdict(lambda: {"chapters": defaultdict(lambda: {"verses": defaultdict(list)})})
    
    for row in cursor.fetchall():
        book_num, chapter, verse, pos, word_id, text, lemma, gloss, lang, required, after = row
        
        books[book_num]["book"] = book_num
        books[book_num]["bookName"] = BIBLE_BOOKS.get(book_num, f"Book {book_num}")
        books[book_num]["language"] = lang
        books[book_num]["chapters"][chapter]["verses"][verse].append({
            "id": word_id,
            "text": text,
            "lemma": lemma,
            "gloss": gloss,
            "after": after or "",
            "position": pos,
            "required": bool(required)
        })
    
    greek_count = 0
    hebrew_count = 0
    
    for book_num, book_data in books.items():
        lang = book_data.get("language", "")
        if lang == "grc":
            folder = APP_DATA_DIR / "sources" / "greek"
            greek_count += 1
        elif lang == "heb":
            folder = APP_DATA_DIR / "sources" / "hebrew"
            hebrew_count += 1
        else:
            continue
        
        output = {
            "book": book_data["book"],
            "bookName": book_data["bookName"],
            "language": lang,
            "chapters": []
        }
        
        for chap_num in sorted(book_data["chapters"].keys()):
            chap_data = book_data["chapters"][chap_num]
            chapter_obj = {"chapter": chap_num, "verses": []}
            
            for verse_num in sorted(chap_data["verses"].keys()):
                words = chap_data["verses"][verse_num]
                chapter_obj["verses"].append({"verse": verse_num, "words": words})
            
            output["chapters"].append(chapter_obj)
        
        book_name = BIBLE_BOOKS.get(book_num, f"book_{book_num}").lower().replace(" ", "_")
        filename = f"{book_num:02d}_{book_name}.json"
        filepath = folder / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"  Greek books: {greek_count}")
    print(f"  Hebrew books: {hebrew_count}")
    print("✓ Source text exported")
    return True


def export_target_text(conn, project_id):
    """Export target language text to JSON files."""
    print(f"\n=== Exporting target text for {project_id} ===")
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT position_book, position_chapter, position_verse, position_word,
               id, text, normalized_text, gloss, language_id, after
        FROM words_or_parts
        WHERE side LIKE 'target%'
          AND ((position_book = 43 AND position_chapter IN (1,2,3)) OR
               (position_book = 45 AND position_chapter IN (1,2,3,4,5,6,7,8)) OR
               (position_book = 40 AND position_chapter IN (5,6,7)))
        ORDER BY position_book, position_chapter, position_verse, position_word
    """)
    
    books = defaultdict(lambda: {"chapters": defaultdict(lambda: {"verses": defaultdict(list)})})
    
    for row in cursor.fetchall():
        book_num, chapter, verse, pos, word_id, text, normalized, gloss, lang, after = row
        
        books[book_num]["book"] = book_num
        books[book_num]["bookName"] = BIBLE_BOOKS.get(book_num, f"Book {book_num}")
        books[book_num]["language"] = lang
        books[book_num]["chapters"][chapter]["verses"][verse].append({
            "id": word_id,
            "text": text,
            "normalized": normalized,
            "gloss": gloss or "",
            "after": after or "",
            "position": pos
        })
    
    folder = APP_DATA_DIR / "targets" / project_id
    book_count = 0
    
    for book_num, book_data in books.items():
        output = {
            "book": book_data["book"],
            "bookName": book_data["bookName"],
            "language": book_data.get("language", ""),
            "chapters": []
        }
        
        for chap_num in sorted(book_data["chapters"].keys()):
            chap_data = book_data["chapters"][chap_num]
            chapter_obj = {"chapter": chap_num, "verses": []}
            
            for verse_num in sorted(chap_data["verses"].keys()):
                words = chap_data["verses"][verse_num]
                chapter_obj["verses"].append({"verse": verse_num, "words": words})
            
            output["chapters"].append(chapter_obj)
        
        book_name = BIBLE_BOOKS.get(book_num, f"book_{book_num}").lower().replace(" ", "_")
        filename = f"{book_num:02d}_{book_name}.json"
        filepath = folder / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        book_count += 1
    
    print(f"  Target books: {book_count}")
    return book_count


def export_alignments(conn, project_id):
    """Export alignment data from links table."""
    print(f"\n=== Exporting alignments for {project_id} ===")
    
    cursor = conn.cursor()
    
    # Build multiple lookup tables for robust matching:
    # 1. Exact text match (case-sensitive)
    # 2. Lowercase text match (case-insensitive)
    # 3. Lemma match (for lemma-based links)
    
    cursor.execute("""
        SELECT text, lemma, position_book, id
        FROM words_or_parts
        WHERE side = 'sources'
    """)
    
    text_to_book = {}        # exact text -> (book, word_id)
    text_lower_to_book = {}  # lowercase text -> (book, word_id)
    lemma_to_book = {}       # lemma -> (book, word_id)
    
    for text, lemma, book, word_id in cursor.fetchall():
        if text and text not in text_to_book:
            text_to_book[text] = (book, word_id)
        if text:
            text_lower = text.lower()
            if text_lower not in text_lower_to_book:
                text_lower_to_book[text_lower] = (book, word_id)
        if lemma and lemma not in lemma_to_book:
            lemma_to_book[lemma] = (book, word_id)
    
    print(f"  Lookup tables built:")
    print(f"    Exact text: {len(text_to_book):,}")
    print(f"    Lowercase: {len(text_lower_to_book):,}")
    print(f"    Lemmas: {len(lemma_to_book):,}")
    
    # Get alignment links from database
    cursor.execute("""
        SELECT id, sources_text, targets_text, origin, status
        FROM links
    """)
    
    books = defaultdict(list)
    total_count = 0
    match_stats = {"exact": 0, "lowercase": 0, "lemma": 0, "unmatched": 0}
    
    for row in cursor.fetchall():
        link_id, sources_text, targets_text, origin, status = row
        
        if not sources_text:
            continue
        
        # The sources_text may be:
        # 1. Single word: "λόγος"
        # 2. Comma-separated: "λόγος,θεός" (m:1 or m:n)
        # 3. Space-separated: "υἱὸς ἀνθρώπου" (phrase alignment)
        if "," in sources_text:
            source_words = [s.strip() for s in sources_text.split(",")]
        elif " " in sources_text:
            source_words = sources_text.split()  # Split multi-word phrase
        else:
            source_words = [sources_text.strip()]
        
        # Same for target text
        if targets_text:
            if "," in targets_text:
                target_words = [t.strip() for t in targets_text.split(",")]
            elif " " in targets_text:
                target_words = targets_text.split()
            else:
                target_words = [targets_text.strip()]
        else:
            target_words = []
        
        # Find book from first source word using fallback strategy
        book_num = None
        source_ids = []
        match_type = None
        
        for word in source_words:
            # Try exact match first
            if word in text_to_book:
                book, word_id = text_to_book[word]
                if book_num is None:
                    book_num = book
                    match_type = "exact"
                source_ids.append(word_id)
            # Try case-insensitive match
            elif word.lower() in text_lower_to_book:
                book, word_id = text_lower_to_book[word.lower()]
                if book_num is None:
                    book_num = book
                    match_type = "lowercase"
                source_ids.append(word_id)
            # Try lemma match
            elif word in lemma_to_book:
                book, word_id = lemma_to_book[word]
                if book_num is None:
                    book_num = book
                    match_type = "lemma"
                source_ids.append(word_id)
        
        if book_num is None:
            match_stats["unmatched"] += 1
            continue
        
        match_stats[match_type] += 1
        
        books[book_num].append({
            "id": link_id,
            "sourceText": source_words,
            "targetText": target_words,
            "sourceIds": source_ids,
            "origin": origin,
            "status": status
        })
        total_count += 1
    
    folder = APP_DATA_DIR / "alignments" / project_id
    
    for book_num, records in books.items():
        book_name = BIBLE_BOOKS.get(book_num, f"book_{book_num}").lower().replace(" ", "_")
        filename = f"{book_num:02d}_{book_name}.json"
        filepath = folder / filename
        
        output = {
            "type": "translation",
            "book": book_num,
            "bookName": BIBLE_BOOKS.get(book_num, f"Book {book_num}"),
            "records": records
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    
    if match_stats["unmatched"] > 0:
        print(f"  Match breakdown:")
        print(f"    Exact match: {match_stats['exact']:,}")
        print(f"    Case-insensitive: {match_stats['lowercase']:,}")
        print(f"    Lemma match: {match_stats['lemma']:,}")
        print(f"    Unmatched: {match_stats['unmatched']:,}")
    print(f"  Books with alignments: {len(books)}")
    print(f"  Total alignment records: {total_count}")
    return len(books), total_count


def download_dictionaries():
    """Download UBS dictionaries."""
    print("\n=== Downloading UBS dictionaries ===")
    
    dict_folder = APP_DATA_DIR / "dictionaries"
    dict_folder.mkdir(parents=True, exist_ok=True)
    
    for filename, url in UBS_DICTIONARIES.items():
        filepath = dict_folder / filename
        
        if filepath.exists():
            print(f"  Skipping (exists): {filename}")
            continue
        
        print(f"  Downloading: {filename}...")
        try:
            urllib.request.urlretrieve(url, filepath)
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"    ✓ {size_mb:.1f} MB")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    print("✓ Dictionaries downloaded")


def main():
    print("=" * 60)
    print("Bible Alignment App - Multi-Database Export")
    print("=" * 60)
    
    # Find all SQLite databases (clear-aligner and demo patterns)
    db_files = list(DATA_DIR.glob("clear-aligner-*.sqlite"))
    db_files.extend(DATA_DIR.glob("demo-*.sqlite"))
    # Exclude the "-updated" variant
    db_files = [f for f in db_files if "-updated" not in f.name]
    
    print(f"\nFound {len(db_files)} databases to process")
    
    if not db_files:
        print("⚠ No databases found!")
        return
    
    # Initialize index
    index = {
        "sources": {
            "greek": {"folder": "sources/greek"},
            "hebrew": {"folder": "sources/hebrew"}
        },
        "dictionaries": {
            "greek": "UBSGreekNTDic-v1.1-en.json",
            "hebrew": "UBSHebrewDic-v0.9.1-en.json"
        },
        "projects": {}
    }
    
    sources_exported = False
    
    # Process each database
    for db_path in sorted(db_files):
        db_filename = db_path.name
        print(f"\n{'='*60}")
        print(f"Processing: {db_filename}")
        print("=" * 60)
        
        conn = sqlite3.connect(db_path)
        
        try:
            # Get project info from database
            project_info = get_project_info(conn, db_filename)
            project_id = project_info["projectId"]
            
            print(f"  Project: {project_info['name']} ({project_id})")
            print(f"  Language: {project_info['language']}")
            
            # Create project folders
            create_project_folders(project_id)
            
            # Export source text (only once, shared across projects)
            sources_exported = export_source_text(conn, sources_exported)
            
            # Export target text
            target_count = export_target_text(conn, project_id)
            
            # Export alignments from database
            align_books, align_count = export_alignments(conn, project_id)
            
            # Add to index
            index["projects"][project_id] = {
                "name": project_info["name"],
                "language": project_info["language"],
                "sourceDatabase": db_filename,
                "targetFolder": f"targets/{project_id}",
                "alignmentFolder": f"alignments/{project_id}",
                "stats": {
                    "targetBooks": target_count,
                    "alignmentBooks": align_books,
                    "alignmentCount": align_count
                },
                "books": []
            }
            
            # Get book details
            alignment_folder = APP_DATA_DIR / "alignments" / project_id
            for filepath in sorted(alignment_folder.glob("*.json")):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                index["projects"][project_id]["books"].append({
                    "book": data.get("book"),
                    "bookName": data.get("bookName"),
                    "alignmentCount": len(data.get("records", [])),
                    "file": filepath.name
                })
            
        finally:
            conn.close()
    
    # Download dictionaries
    download_dictionaries()
    
    # Write index
    print("\n=== Generating index.json ===")
    index_path = APP_DATA_DIR / "index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"  Projects indexed: {len(index['projects'])}")
    print("✓ Index generated")
    
    print("\n" + "=" * 60)
    print("✓ Data preparation complete!")
    print(f"  Output folder: {APP_DATA_DIR}")
    print(f"  Projects: {len(index['projects'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
