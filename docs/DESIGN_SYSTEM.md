# AnimeVerse AI — Design System & UI/UX Architecture

This document defines the visual design system, design tokens, component architecture, and accessibility standards powering **AnimeVerse AI**.

---

## 1. Design Vision & Aesthetic Direction

AnimeVerse AI adopts a **Premium Dark Anime Platform** aesthetic that balances cinematic depth with functional clarity.

### Core Visual Principles
- **Deep Midnight Canvas**: Eliminates harsh pure-white backgrounds in favor of rich midnight and charcoal tones (`#080911`, `#0e101d`, `#131627`), reducing visual fatigue during extended browsing sessions.
- **Purposeful Purple Accents**: Primary accents leverage vibrant purple gradients (`#9333ea`, `#a855f7`, `#c084fc`) complemented by secondary cyan (`#06b6d4`) and amber (`#f59e0b`) highlights. Neon effects are strictly restrained to indicators, active pills, and glows.
- **Balanced Glassmorphism**: Cards and floating panels utilize multi-layer alpha blurs (`backdrop-blur-md`, `bg-[#0e101d]/90`, `border-purple-500/20`) rather than high-contrast solid borders.
- **Restrained Motion**: Micro-interactions provide tactile responsiveness without disorienting layout shifts. Motion strictly respects user accessibility preferences (`prefers-reduced-motion: reduce`).

---

## 2. Design Tokens

### 2.1 Color Tokens
The platform defines semantic color variables in `frontend/src/index.css`:

```css
:root {
  /* Surface & Background Tokens */
  --bg-primary: #080911;          /* Root canvas midnight black */
  --bg-secondary: #0e101d;        /* Secondary panels and containers */
  --bg-card: #131627;             /* Elevated cards and list rows */
  --bg-glass: rgba(14, 16, 29, 0.85); /* Glassmorphic overlays */
  --bg-input: #080911;            /* Form input field backgrounds */

  /* Border & Elevation Tokens */
  --border-subtle: rgba(168, 85, 247, 0.15); /* Baseline card separation */
  --border-card: rgba(168, 85, 247, 0.25);   /* Interactive card borders */
  --border-active: #a855f7;                  /* Focused / active element borders */

  /* Primary Accent & Semantic Colors */
  --accent-purple: #9333ea;       /* Base brand purple */
  --accent-purple-light: #a855f7; /* Hover / highlight purple */
  --accent-cyan: #06b6d4;         /* Telemetry & streaming badge cyan */
  --accent-emerald: #10b981;      /* Completed / verified green */
  --accent-amber: #f59e0b;        /* Rating / spoiler warning amber */
  --accent-rose: #f43f5e;         /* Error / destructive action rose */

  /* Typography Colors */
  --text-primary: #f8fafc;        /* High-contrast headings and active labels */
  --text-secondary: #94a3b8;      /* Body copy and secondary metrics */
  --text-muted: #64748b;          /* Metadata timestamps and hints */
  --text-accent: #c084fc;         /* Interactive links and highlighted text */
}
```

### 2.2 Typography Scale
Typography pairs **Inter** (sans-serif) for body and headings with **JetBrains Mono** / **Roboto Mono** for telemetry, statistics, episode counts, and tags.

| Token | Class | Size | Font Weight | Primary Usage |
| :--- | :--- | :--- | :--- | :--- |
| `display-1` | `text-4xl sm:text-5xl` | 36px / 48px | 800 (Extra Bold) | Hero titles, major banner headings |
| `display-2` | `text-2xl sm:text-3xl` | 24px / 30px | 800 (Extra Bold) | Page titles (`Dashboard`, `Discover`, `RYUK`) |
| `heading-1` | `text-xl sm:text-2xl` | 20px / 24px | 700 (Bold) | Section headers, modal dialog titles |
| `heading-2` | `text-base sm:text-lg` | 16px / 18px | 700 (Bold) | Carousel headers, post titles |
| `body-base` | `text-sm` | 14px | 400 (Normal) | Primary synopsis, review bodies, comments |
| `body-small`| `text-xs` | 12px | 400 / 500 | Card descriptions, secondary text |
| `caption`   | `text-[11px]` | 11px | 400 / 600 | Metadata stamps, sublabels |
| `badge-mono`| `text-[10px] font-mono`| 10px | 700 (Bold) | Episode badges, status tags, MAL scores |

### 2.3 Spacing & Grid System
AnimeVerse AI is built on a 4px/8px modular spacing grid:
- `p-1` (4px) / `p-2` (8px) / `p-3` (12px) / `p-4` (16px) / `p-5` (20px) / `p-6` (24px) / `p-8` (32px) / `p-10` (40px)
- Page layouts utilize standard vertical spacing: `space-y-6 sm:space-y-8 lg:space-y-10`.
- Card grids adapt dynamically:
  - Desktop (1440px): 5 columns (`grid-cols-5`)
  - Laptop (1024px): 4 columns (`grid-cols-4`)
  - Tablet (768px): 3 columns (`grid-cols-3`)
  - Mobile (360px - 390px): 2 columns (`grid-cols-2`)

### 2.4 Border Radius Hierarchy
- Small elements (Tags, badges, tooltips): `rounded-lg` (8px)
- Medium components (Buttons, inputs, dropdowns): `rounded-xl` (12px)
- Cards & Content panels: `rounded-2xl` (16px)
- Hero banners & Modals: `rounded-3xl` (24px)
- Round icons & avatars: `rounded-full` (9999px)

### 2.5 Elevation & Shadow Layers
1. **Canvas Level (Elevation 0)**: Background `#080911` with subtle cyber-grid backdrop.
2. **Surface Level (Elevation 1)**: Panels and sidebars `#0e101d` with `border border-purple-500/20`.
3. **Card Level (Elevation 2)**: Floating cards `#131627` with `shadow-[0_0_20px_rgba(168,85,247,0.12)]`.
4. **Interactive Hover (Elevation 3)**: `hover:-translate-y-1 hover:shadow-[0_0_25px_rgba(168,85,247,0.25)]`.
5. **Modal Overlay (Elevation 4)**: `bg-black/80 backdrop-blur-md` with `shadow-[0_0_50px_rgba(0,0,0,0.8)]`.

---

## 3. Navigation Experience

### 3.1 Desktop Sidebar (`Sidebar.jsx`)
- Fixed vertical navigation bar (`w-64`) with smooth collapsible states.
- **Active Navigation Pill**: Active routes feature a vertical accent indicator pill (`w-1 h-5 bg-gradient-to-b from-purple-400 to-cyan-400 rounded-full`) along the left edge.
- **Accessible Touch Targets**: Every navigation item enforces `min-h-[44px]` with `aria-label` and `role="navigation"`.
- **Keyboard Shortcut Cue**: Displays global `/ for search` cue in status footer.

### 3.2 Top Navigation (`TopNav.jsx`)
- Persistent header with responsive search bar, notifications bell, and user session badge.
- **Mobile Search Drawer**: On screens `< 640px`, a dedicated search button expands an accessible full-width search drawer.
- **User Profile Pill**: Directly routes authenticated users to their taste profile and settings (`/profile`).

### 3.3 Search Bar (`SearchBar.jsx`)
- **Keyboard Navigation**:
  - Global `/` key triggers focus from anywhere on the page (ignoring inputs and textareas).
  - `ArrowDown` and `ArrowUp` navigate through search suggestions.
  - `Enter` immediately selects the highlighted suggestion or submits search.
  - `Escape` dismisses the suggestions list.
- **ARIA Semantics**: Implements `role="combobox"`, `role="listbox"`, `role="option"`, and `aria-selected` attributes.

---

## 4. Component Standards

### 4.1 Anime Card (`AnimeCard.jsx`)
- **Aspect Ratio**: Standardized 3:4 movie poster aspect ratio with `overflow-hidden`.
- **Non-Colliding Badges**: Top left houses score (`★ 8.9`) and format (`TV`), while top right isolates `AddToListButton` with no overlapping z-index conflicts.
- **Typography**: Card titles use `line-clamp-1 font-semibold text-slate-100 hover:text-purple-300`.
- **Hover Lift**: Restrained `-translate-y-1` transition (150ms) with purple border accentuation.

### 4.2 Telemetry Stat Cards (`StatCard.jsx`)
- Minimum height `min-h-[110px]` ensures equal grid heights across viewports.
- Integrated `role="region"` and accessible `aria-label` tags.
- Distinct color accents (`purple`, `cyan`, `emerald`) mapped to specific metrics.

### 4.3 Episode Progress Cards (`ProgressCard.jsx`)
- Accessible episode stepper buttons (`w-7 h-7`) with `aria-label` for screen reader users.
- Custom progress bar featuring `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, and `aria-valuemax`.

### 4.4 RYUK Neural Companion (`RyukAssistantPage.jsx`)
- **User Bubbles**: Purple-to-indigo gradient (`bg-gradient-to-r from-purple-600 to-indigo-600`), high-contrast text, `rounded-tr-sm`.
- **RYUK Assistant Bubbles**: Midnight glass (`bg-[#0e101d]/95`), purple border accent, `rounded-tl-sm`.
- **AI Avatar**: Glowing icon badge with pulse indicator indicating online status.
- **Prompt Suggestion Chips**: Tactile pill buttons with keyboard focus rings and active scale feedback.
- **Input Bar**: Auto-expanding input with helper cue (`Press Enter to send • Shift+Enter for newline`).

---

## 5. Accessibility & Inclusivity (WCAG 2.1 AA)

1. **Global Focus Indicators**:
   All interactive elements enforce accessible visible focus states via `frontend/src/index.css`:
   ```css
   *:focus-visible {
     outline: 2px solid var(--accent-purple-light) !important;
     outline-offset: 2px !important;
   }
   ```
2. **Reduced Motion Query**:
   Users with vestibular disorders or motion sensitivity are respected:
   ```css
   @media (prefers-reduced-motion: reduce) {
     *, *::before, *::after {
       animation-duration: 0.01ms !important;
       transition-duration: 0.01ms !important;
       scroll-behavior: auto !important;
     }
   }
   ```
3. **Contrast Ratios**:
   All critical text achieves contrast ratios exceeding 4.5:1 against midnight card backgrounds:
   - Primary Headings (`#f8fafc` on `#080911`): 18.2:1
   - Secondary Text (`#94a3b8` on `#0e101d`): 6.8:1
   - Purple Accent Text (`#c084fc` on `#080911`): 7.4:1
   - Amber Badges (`#f59e0b` on `#000000`): 9.2:1
4. **Touch Target Sizing**:
   Interactive controls enforce minimum dimensions of 28px - 44px on mobile viewports to prevent mis-taps.

---

## 6. Responsive Viewport Compliance Matrix

| Viewport | Device Target | Sidebar Behavior | Grid Columns | Navigation |
| :--- | :--- | :--- | :--- | :--- |
| **360px** | Ultra-compact Mobile | Bottom/drawer navigation | 2 columns | Mobile drawer search |
| **390px** | Modern Mobile (iPhone 14/15) | Bottom/drawer navigation | 2 columns | Full-width touch search |
| **768px** | Tablet (iPad / Android Tablet) | Collapsed icon bar | 3 columns | Responsive header |
| **1024px** | Small Laptop / Netbook | Persistent 240px sidebar | 4 columns | Integrated search bar |
| **1440px** | Standard Desktop / WQHD | Full 256px sidebar | 5 columns | Global keyboard shortcuts |
| **1920px** | Large Desktop / Ultra-wide | Full 256px sidebar (max container) | 5-6 columns | Centered max-w canvas |

---

*AnimeVerse AI Design System — Version 1.0.0 (Phase 13)*
