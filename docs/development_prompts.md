# ScriptureLens - Development Prompts (React)

Prompts for building the React version based on Streamlit prototype learnings.

---

## Phase 1: Project Setup

### 1.1 - Initialize React Project
```
Create a React + Vite + TypeScript project with Tailwind CSS and ShadCN UI.
- Folder structure: /src/pages, /src/components, /src/lib, /src/api
- React Router with tab-based navigation (not sidebar)
- Layout with header (project selector) and dynamic sidebar
- Path aliases (@/components, @/lib)
```

### 1.2 - Data Layer
```
Create data layer to load JSON exports from Streamlit app:
- Types: Word, Alignment, Project, LemmaIndex
- API functions: fetchProject, fetchText, fetchAlignments
- React Query hooks: useProject, useChapter, useConcordance
- DataContext for global project state
```

---

## Phase 2: Core Pages

### 2.1 - Scripture Page (Landing)
```
Create Scripture reader as the landing page:
- Clean verse-by-verse target text display
- Verse numbers in blue
- Hover tooltips showing source word, lemma, gloss
- Sidebar: Book selector, chapter nav (◀ N ▶), "Show source" toggle
- Font: Gentium Plus (Google Fonts) for proper script display
```

### 2.2 - Interlinear Page
```
BibleHub-style interlinear with two layouts:

Card Layout:
- Vertical word stacks: Source (blue) → Lemma (italic) → Gloss → Target (green)
- ~8 words per row, responsive
- Green left border = aligned, Orange = unaligned
- Hover tooltip with alignment details

Grid Layout:
- Compact flowing view with source/target only
- Dashed border for unaligned words
- Smaller font, more words visible

Sidebar controls:
- Book/Chapter selectors
- Reverse toggle (target-word order)
- Layout toggle (Card/Grid)
- Words per row slider
```

### 2.3 - Concordance Page
```
3-column master-detail layout:
- Column 1: Lemma list with gloss and frequency (filterable NT/OT)
- Column 2: Target renderings (lazy load on lemma click)
- Column 3: Verse context with KWIC highlighting

Controls:
- Testament filter (horizontal radio)
- Max lemmas slider
- Context words slider
- AI Word Study button (uses LLM)
```

---

## Phase 3: Analytics Pages

### 3.1 - Completion Overview
```
Charts showing alignment progress:
- Bar chart: Completion % by book
- Pie chart: Status distribution (approved/created/missing)
- Testament filter
- Drill-down links to specific books
```

### 3.2 - Drill-down
```
Filterable alignment table:
- Filters: Testament, Book, Chapter, Status
- Table: Source, Target, Status, Reference
- Search box for source/target text
- Pagination
```

---

## Phase 4: Settings & LLM

### 4.1 - Settings Page (Tabs)
```
Appearance Tab:
- Font selector (Inter, Roboto, Gentium Plus, etc.)
- Font size (Small/Medium/Large)
- Primary/Accent color pickers
- Theme toggle (Light/Dark)
- Preview box

Data Tab:
- Data path configuration
- Sync button with last-sync time
- Project list with stats

AI Tab:
- Default provider selector
- Provider cards with model selection
- Test connection button per provider
```

### 4.2 - LLM Integration
```
Multi-provider LLM support:
- Providers: OpenAI, Gemini, Anthropic, Ollama, Custom
- Config via .env file
- Test connection endpoint
- AI Word Study feature in Concordance
- Provider abstraction layer
```

---

## Phase 5: Future Features

### 5.1 - Alignment Editor
```
Dedicated editor page for creating/editing alignments:
- Source panel (left) + Target panel (right)
- Click-to-link word selection
- Cross-verse alignments
- Status management (created/approved)
- Auto-save with debounce
```

### 5.2 - Git Integration
```
Version control for collaborative editing:
- Commit button with message
- Push/Pull operations
- Conflict detection and resolution UI
```
