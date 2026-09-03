---
kind: frontend_style
name: CSS Design Tokens, Scoped Class System & Dual-Themed Admin/Student UI
category: frontend_style
scope:
    - '**'
source_files:
    - src/styles/tokens.css
    - src/styles/base.css
    - src/styles/layout.css
    - src/styles/components.css
    - src/styles/student.css
    - src/styles/index.css
    - src/App.jsx
    - package.json
---

## What system/approach is used

The frontend styling is a **hand-authored CSS design-token system** built on native CSS custom properties (variables), with no CSS-in-JS library, no Tailwind, and no external component library. The app is a React SPA built with Vite; styles are plain `.css` files imported once from `src/styles/index.css`, which chains them in strict order: tokens → base → layout → components → student.

Two visual surfaces share the same token set but have separate style entry points:
- **Admin console** — dense, data-heavy interface under `/admin`, scoped to the `.uaea[data-theme]` root element.
- **Student site** — lighter, mobile-first experience at `/`, scoped to a `.st` root.

Theme switching is done by toggling `data-theme="light"` / `data-theme="dark"` on the `.uaea` root; both palettes are defined side-by-side in `tokens.css`. A `prefers-reduced-motion` media query globally disables animations for users who asked the OS to calm down.

## Key files and packages

- `src/styles/tokens.css` — all design tokens: colors (`--brass`, `--jade`, `--amber`, `--rose`, `--sky`, `--violet`), surface/typography tokens (`--bg`, `--panel`, `--t1`..`--t3`), spacing/radius (`--r-sm`, `--r`, `--r-lg`), layout constants (`--sidebar`, `--topbar`), shadows, scrollers, and light/dark theme blocks.
- `src/styles/base.css` — resets, typography (`Inter` + Urdu `Noto Naskh Arabic`), focus ring, shared keyframes (`ua-fade-in`, `ua-pop-in`, `ua-slide-in`, `ua-shimmer`, `ua-spin`, `ua-draw`), scrollbar styling, reduced-motion enforcement.
- `src/styles/layout.css` — admin shell (`.ua-shell`, `.ua-side`, `.ua-top`, `.ua-page`), sidebar collapse, ambient glow, page grids, mobile drawer behavior.
- `src/styles/components.css` — reusable primitives: cards (`.ua-card`), badges (`.ua-badge.jade|amber|rose|sky|violet|brass|grey`), buttons (`.ua-btn.primary|ghost|danger|sm|block`), inputs/selects/textareas, switches, tabs/toolbars, tables/pagination/bulk bar, empty states, overlays/modals/drawers, command palette, toasts, notes/diffs, progress/skeleton, chart SVG classes (`.ch-*`), guided-flow step editor.
- `src/styles/student.css` — student-facing layer (`.` prefixed with `st-`) with its own header, hero, ask bar, chat bubbles, composer, routing card, source/freshness display, detail pages, footer.
- `src/styles/index.css` — single import chain that enforces token-first ordering.
- `package.json` — only runtime deps are `react`, `react-dom`, `react-router-dom`, `lucide-react`; no CSS framework or preprocessor in devDependencies.

## Architecture and conventions

1. **Token-driven theming.** Every color, radius, shadow, and semantic surface is a CSS variable. Components never hard-code hex values for meaning-bearing visuals; they read `var(--brass)`, `var(--jade-soft)`, `var(--sh-2)`, etc. This makes the light/dark toggle a pure class swap on the root element.

2. **Scoped class namespaces.**
   - Admin UI uses a `ua-` prefix (e.g. `.ua-card`, `.ua-btn`, `.ua-table`).
   - Student UI uses a `st-` prefix (e.g. `.st-card`, `.st-chat`, `.st-composer`).
   - Chart SVGs use a `ch-` prefix so charts re-theme automatically without inline styles.
   - Animations use a `ua-` prefix (`ua-spin`, `ua-fade-in`, …).

3. **Semantic color vocabulary.** The token comment explicitly defines meaning: brass is the accent, jade means "a human vouched for this" and is never decoration, and `-bright` variants are reserved for fills/charts while `-soft`/`-line` variants are backgrounds/borders. Badges and notes compose these semantics via modifier classes (`.jade`, `.amber`, `.rose`, …).

4. **Component composition over monolithic blocks.** Primitives like `.ua-btn`, `.ua-field`, `.ua-input`, `.ua-modal-h/.ua-modal-b/.ua-modal-f` are combined by page components rather than each page writing its own button or modal styles.

5. **Responsive strategy is CSS-only.** Breakpoints live in `layout.css` and `student.css` using `@media (min-width|max-width)` to switch between single-column mobile layouts and multi-column desktop grids (`.ua-cols.two`, `.ua-split`, `.st-grid.three`, etc.). No JS-based responsive logic is present in the style layer.

6. **Accessibility hooks baked into base.** `:focus-visible` gets a brass outline, `prefers-reduced-motion` zeroes animation/transition durations, Urdu text gets isolated RTL direction via `.ur`, and tabular numbers use `font-variant-numeric: tabular-nums` wherever columns of digits appear.

7. **Dual-root architecture.** `App.jsx` renders two independent shells sharing one data layer: `<StudentShell />` for `/` and `<AppShell />` for `/admin`. Each shell owns its own CSS namespace so the two experiences can diverge in pacing and density while staying visually consistent through shared tokens.

## Conventions and constraints

- **All colors flow through tokens.** Hard-coded brand colors in components (e.g. the brass gradient on `.ua-btn.primary` and `.st-send`) are exceptions documented as part of the brand identity; semantic surfaces must still use variables.
- **New UI elements should extend existing primitives.** Buttons, badges, cards, modals, and tables already cover most patterns; new features should reuse those classes plus token variables rather than inventing new ones.
- **Theme scope is enforced by root classes.** Admin code must wrap itself in an element with class `uaea` (and optionally `data-theme`), student code in `.st`. Cross-contamination between the two namespaces is prevented by the prefixes.
- **Animations are opt-out friendly.** Any new animation should be wrapped in a keyframe defined in `base.css` and respected by the `prefers-reduced-motion` block that zeroes durations globally.
- **Charts paint via CSS classes.** SVG chart elements use `.ch-*` classes mapped to token variables so they automatically follow the active theme without JavaScript color management.
- **No preprocessors or build-time CSS transforms.** The stack is plain CSS consumed by Vite; there is no Sass/Less/PostCSS configuration visible in the repo.