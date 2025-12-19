# ScriptureLens - Discovery Summary

**Date:** 2025-12-19 (Updated)
**Status:** Streamlit prototype complete, React migration planned

---

## What We Built (Streamlit v1.0)

### 8 Pages
1. **Scripture** - Clean reading view with hover tooltips
2. **Interlinear** - BibleHub-style word stacks (Card/Grid)
3. **Concordance** - 3-column lemma explorer with AI Word Study
4. **Drill-down** - Filtered alignment table
5. **Completion** - Progress charts
6. **Comparison** - Side-by-side projects
7. **Database** - SQL explorer
8. **Settings** - Font, colors, LLM providers

### Key Features
- Multi-project support (Bengali, Hindi, etc.)
- Dynamic sidebar per page
- Reverse interlinear toggle
- LLM integration (OpenAI, Gemini, Anthropic, Ollama)
- Font/theme customization
- Hover tooltips with alignment info

---

## User Workflows Validated

### Scripture Reading
```
1. Open app → Scripture page (landing)
2. Select book/chapter in sidebar
3. Read target text verse by verse
4. Hover words to see source alignment
5. Toggle "Show source" for detailed view
```

### Interlinear Study
```
1. Navigate to Interlinear tab
2. Select book/chapter
3. View word stacks: Source → Lemma → Gloss → Target
4. Toggle Reverse for target-order view
5. Switch Card ↔ Grid layout as needed
```

### Concordance Research
```
1. Go to Concordance tab
2. Select NT/OT filter
3. Click lemma → see renderings
4. Click rendering → see verse context
5. Click "AI Word Study" for LLM analysis
```

---

## Design Decisions Made

| Decision                     | Rationale                             |
| ---------------------------- | ------------------------------------- |
| Tab navigation (not sidebar) | More screen space for content         |
| Scripture as landing page    | Most natural starting point           |
| BibleHub-style interlinear   | Familiar to Bible students            |
| Dynamic sidebar per page     | Page-specific controls                |
| Hover tooltips               | Less cluttered than inline            |
| Card + Grid layouts          | User preference                       |
| Reverse interlinear          | Essential for target-language readers |

---

## Lessons for React Version

1. **BibleHub layout** preferred over table
2. **Dynamic sidebar** works well for filters
3. **Font matters** - Gentium Plus recommended
4. **Tooltips** > inline annotations
5. **Reverse interlinear** is essential
6. **Scripture reader** should be default page
7. **AI features** enhance research workflow

---

## Next Steps: React Migration

1. Set up React + Vite + Tailwind + ShadCN
2. Create JSON export from current data
3. Port pages in order: Scripture → Interlinear → Concordance
4. Add Express backend for data API
5. Implement offline mode with Service Workers
6. Add alignment editor (new feature)
7. Git integration for collaboration
