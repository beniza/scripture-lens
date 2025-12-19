# ScriptureLens - Project Overview

## Current State (v1.0 - Streamlit Prototype)

**ScriptureLens** is a Bible translation alignment viewer built with Streamlit. It provides visualization and analysis tools for reviewing Clear Aligner data.

### Pages Implemented

| Page          | Description                                    | Status     |
| ------------- | ---------------------------------------------- | ---------- |
| 📜 Scripture   | Clean reading view with alignment tooltips     | ✅ Complete |
| 📖 Interlinear | BibleHub-style word stacks (Card/Grid layouts) | ✅ Complete |
| 📚 Concordance | 3-column lemma → rendering → context view      | ✅ Complete |
| 🔍 Drill-down  | Filtered alignment table with search           | ✅ Complete |
| 📊 Completion  | Progress charts by book/chapter                | ✅ Complete |
| 🔄 Comparison  | Side-by-side project comparison                | ✅ Complete |
| 🗄️ Database    | SQL query explorer                             | ✅ Complete |
| ⚙️ Settings    | Font, colors, LLM providers, data sync         | ✅ Complete |

### Features Implemented

- **Multi-project support** (Bengali, Hindi, etc.)
- **Dynamic sidebar** per page with filters/settings
- **Reverse interlinear** toggle (target-word order)
- **AI Word Study** via LLM integration
- **Font/theme customization**
- **Hover tooltips** with alignment info

---

## Data Architecture

### Source: Clear Aligner SQLite
```
data/
└── clear-aligner-*.sqlite
    ├── words_or_parts (sources + targets)
    ├── links (alignment connections)
    └── links__source_words / links__target_words
```

### Export: JSON for React
```
app_data/
├── index.json           # Project metadata
├── sources/greek/       # NT source texts
├── sources/hebrew/      # OT source texts  
├── targets/{project}/   # Target texts
└── alignments/{project}/ # Alignment links
```

---

## Tech Stack

| Layer    | Streamlit (Current)               | React (Planned)                  |
| -------- | --------------------------------- | -------------------------------- |
| Frontend | Streamlit                         | React + Vite + Tailwind + ShadCN |
| State    | st.session_state                  | React Query + Context            |
| Data     | SQLite (read-only)                | JSON files + Express API         |
| LLM      | OpenAI, Gemini, Anthropic, Ollama | Same providers                   |
| Offline  | N/A                               | Service Workers + IndexedDB      |

---

## Key Learnings from Prototype

1. **BibleHub-style interlinear** is preferred over table layout
2. **Dynamic sidebar** for page-specific controls works well
3. **Reverse interlinear** (target-order) is essential
4. **Hover tooltips** more effective than inline display
5. **Card/Grid layout toggle** gives users flexibility
6. **Scripture reader** should be the landing page

---

## Next: React Migration

See [architecture.md](architecture.md) for React architecture.
See [development_prompts.md](development_prompts.md) for implementation prompts.
