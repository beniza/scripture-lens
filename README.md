# Alignment Dashboard

A Streamlit-based dashboard for visualizing and analyzing Bible translation alignment data from Clear Aligner.

## Features

### 📊 Drill-down Analytics
- Filter by Testament, Book, Chapter, Verse
- View source/target word alignments with status

### 📈 Completion Overview
- Completion percentage by book (bar chart)
- Link status distribution (stacked bar)
- Detailed summary table

### 📖 Interlinear View
- Verse-by-verse display with source/target alignment
- Toggle between Source Order and Target Order
- Shows required words (✱), linked status
- Deep-linking support via URL params (e.g., `?book=58&chapter=3`)

### 📚 Concordance
- **3-column master-detail layout**:
  - Column 1: Lemmas with glosses (Greek/Hebrew)
  - Column 2: Target renderings (lazy-loaded on click)
  - Column 3: Verse context with KWIC (lazy-loaded on click)
- NT (Greek) / OT (Hebrew) toggle
- Configurable context word count
- Click-through to Interlinear View

## Setup

```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run app.py
```

## Data

Place SQLite database files from Clear Aligner in the `data/` folder. The dashboard will auto-detect them.

## Tech Stack

- **Streamlit** - Web UI framework
- **Pandas** - Data manipulation
- **Plotly** - Charts and visualizations
- **SQLite** - Database backend
