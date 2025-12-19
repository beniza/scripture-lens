"""
Concordance Index Generator

Creates pre-computed lemma indexes for fast concordance lookups:
- app_data/concordance/nt_lemmas.json (Greek NT)
- app_data/concordance/ot_lemmas.json (Hebrew OT)

Each lemma entry includes:
- gloss (from source data)
- frequency (total occurrences)
- occurrences (book, chapter, verse, word position, text)
- renderings (target language translations with frequencies, per project)
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

APP_DATA_DIR = Path(__file__).parent / "app_data"


def build_source_concordance(testament):
    """Build concordance from source text files."""
    if testament == "nt":
        source_folder = APP_DATA_DIR / "sources" / "greek"
        lang = "grc"
    else:
        source_folder = APP_DATA_DIR / "sources" / "hebrew"
        lang = "heb"
    
    # lemma -> { gloss, occurrences: [{book, chapter, verse, position, text, wordId}] }
    concordance = defaultdict(lambda: {
        "lemma": "",
        "gloss": "",
        "language": lang,
        "frequency": 0,
        "occurrences": []
    })
    
    for filepath in sorted(source_folder.glob("*.json")):
        with open(filepath, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
        
        book_num = book_data["book"]
        book_name = book_data["bookName"]
        
        for chapter in book_data.get("chapters", []):
            chapter_num = chapter["chapter"]
            
            for verse in chapter.get("verses", []):
                verse_num = verse["verse"]
                
                for word in verse.get("words", []):
                    lemma = word.get("lemma", "")
                    if not lemma:
                        continue
                    
                    concordance[lemma]["lemma"] = lemma
                    concordance[lemma]["gloss"] = word.get("gloss", "")
                    concordance[lemma]["language"] = lang
                    concordance[lemma]["frequency"] += 1
                    concordance[lemma]["occurrences"].append({
                        "book": book_num,
                        "bookName": book_name,
                        "chapter": chapter_num,
                        "verse": verse_num,
                        "position": word.get("position", 0),
                        "text": word.get("text", ""),
                        "wordId": word.get("id", ""),
                        "required": word.get("required", False)
                    })
    
    return dict(concordance)


def add_renderings(concordance, testament):
    """Add target language renderings from alignments."""
    
    # Load index to get projects
    index_path = APP_DATA_DIR / "index.json"
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    # Build word text -> lemma lookup from source occurrences
    text_to_lemma = {}
    for lemma, data in concordance.items():
        for occ in data["occurrences"]:
            text_to_lemma[occ["text"]] = lemma
    
    # Process each project
    for proj_id, proj in index.get("projects", {}).items():
        print(f"  Adding renderings from {proj_id}...")
        
        alignment_folder = APP_DATA_DIR / "alignments" / proj_id
        if not alignment_folder.exists():
            continue
        
        # Determine which testament this project covers
        # Check first alignment file to see book range
        align_files = list(alignment_folder.glob("*.json"))
        if not align_files:
            continue
        
        # Initialize renderings dict for each lemma
        for lemma in concordance:
            if "renderings" not in concordance[lemma]:
                concordance[lemma]["renderings"] = {}
            if proj_id not in concordance[lemma]["renderings"]:
                concordance[lemma]["renderings"][proj_id] = {}
        
        # Process alignment files
        for filepath in align_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                align_data = json.load(f)
            
            book_num = align_data.get("book", 0)
            
            # Skip if wrong testament
            if testament == "nt" and book_num < 40:
                continue
            if testament == "ot" and book_num >= 40:
                continue
            
            for record in align_data.get("records", []):
                source_texts = record.get("sourceText", [])
                target_texts = record.get("targetText", [])
                
                if not source_texts or not target_texts:
                    continue
                
                # Join target words into rendering
                rendering = " ".join(target_texts)
                
                # Find lemma for each source word and add rendering
                for source_text in source_texts:
                    if source_text in text_to_lemma:
                        lemma = text_to_lemma[source_text]
                        
                        if rendering not in concordance[lemma]["renderings"][proj_id]:
                            concordance[lemma]["renderings"][proj_id][rendering] = 0
                        concordance[lemma]["renderings"][proj_id][rendering] += 1
    
    # Convert rendering dicts to sorted lists
    for lemma in concordance:
        if "renderings" in concordance[lemma]:
            for proj_id in concordance[lemma]["renderings"]:
                renderings = concordance[lemma]["renderings"][proj_id]
                # Convert to sorted list by frequency
                sorted_renderings = sorted(
                    [{"text": k, "count": v} for k, v in renderings.items()],
                    key=lambda x: -x["count"]
                )
                concordance[lemma]["renderings"][proj_id] = sorted_renderings
    
    return concordance


def save_concordance(concordance, testament):
    """Save concordance to JSON file."""
    output_folder = APP_DATA_DIR / "concordance"
    output_folder.mkdir(parents=True, exist_ok=True)
    
    filename = f"{testament}_lemmas.json"
    filepath = output_folder / filename
    
    # Sort by frequency descending
    sorted_concordance = dict(
        sorted(concordance.items(), key=lambda x: -x[1]["frequency"])
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(sorted_concordance, f, ensure_ascii=False, indent=2)
    
    return filepath


def generate_summary(concordance, testament):
    """Generate summary statistics."""
    total_lemmas = len(concordance)
    total_occurrences = sum(c["frequency"] for c in concordance.values())
    
    # Top 10 most frequent
    top_10 = sorted(concordance.values(), key=lambda x: -x["frequency"])[:10]
    
    print(f"\n  {testament.upper()} Summary:")
    print(f"    Unique lemmas: {total_lemmas:,}")
    print(f"    Total occurrences: {total_occurrences:,}")
    print(f"    Top 10 lemmas:")
    for item in top_10:
        print(f"      {item['lemma']}: {item['frequency']:,} ({item['gloss']})")


def main():
    print("=" * 60)
    print("Concordance Index Generator")
    print("=" * 60)
    
    for testament in ["nt", "ot"]:
        print(f"\n=== Building {testament.upper()} Concordance ===")
        
        # Build base concordance from source files
        print("  Indexing source lemmas...")
        concordance = build_source_concordance(testament)
        print(f"    Found {len(concordance):,} unique lemmas")
        
        # Add target language renderings
        print("  Adding target renderings...")
        concordance = add_renderings(concordance, testament)
        
        # Save to file
        filepath = save_concordance(concordance, testament)
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"  Saved: {filepath.name} ({size_mb:.1f} MB)")
        
        # Show summary
        generate_summary(concordance, testament)
    
    print("\n" + "=" * 60)
    print("✓ Concordance generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
