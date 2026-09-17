# CLAUDE.md

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored to prevent locally-configured registries from leaking into commits — leave both in place.

## Critical Tool Usage Rules

### Subagents
Use the Task tool with these specialized subagents for appropriate tasks:

- **vue-expert**: Use for Vue 3 frontend features, UI components, styling, and client-side functionality
  - Examples: Creating components, fixing reactivity issues, performance optimization, complex state management
  - **MANDATORY RULE: ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert**
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **Explore**: Use for understanding codebase structure, searching for patterns, or answering questions about how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test** skill: Use when writing or modifying tests in `tests/backend` directory with pytest and FastAPI TestClient

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded via `server/mock_data.py`

## Quick Start

```bash
# Backend
cd server
uv run python main.py

# Frontend
cd client
npm install && npm run dev
```

## Code Conventions
- Always document non-obvious logic changes with comments

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

## File Locations
- Views: `client/src/views/*.vue`
- API Client: `client/src/api.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Design tokens: `client/src/styles/tokens.css` (spacing, type, color, radius, elevation, chart series)
- Shared primitives: `client/src/styles/primitives.css` (card, table, badge, button, form, states)
- App shell + migration shims: `client/src/App.vue`
- Sidebar: `client/src/components/AppSidebar.vue` (nav comes from `meta.nav` in `main.js`)

## Design System

Token-based. **Never introduce a raw hex value or a hardcoded padding in a component** —
if a value is missing, add it to `tokens.css` and use the token. That rule is the
only thing keeping the app from drifting back into seven independently styled screens.

- **Layout**: fixed left sidebar (`AppSidebar.vue`) + content column offset by
  `--sidebar-width`. Navigation lives in the sidebar; per-page controls live with
  the page. Add a route to `main.js` with `meta.nav` and it appears in the nav.
- **Spacing/type**: `var(--space-*)` on a 4px ladder, `var(--text-*)`. Two or three
  type sizes per screen.
- **Color**: one accent (`--color-accent`). Status colors (`--success-*`, `--warning-*`,
  `--danger-*`, `--info-*`) are reserved for state and always pair with a word, never
  colour alone. Chart series use `--series-1..6` in fixed order — never status hues.
- **Surfaces**: build from `.card`, `.stat-card`, `.data-table`, `.badge`, `.btn`,
  `.input`, `.state`. Numeric columns get `class="num"` on both `<th>` and `<td>`.
- **Narrow screens**: write every flexible grid track as `minmax(0, 1fr)`, never
  bare `1fr`. A bare track floors at its content's min-content width, so one wide
  table silently stretches the whole page sideways on a phone — and a screenshot
  won't show it, because the image just crops. Verify with
  `document.documentElement.scrollWidth === clientWidth` at 390px.
- **States**: loading / empty / error are part of the design. Empty states say what
  would appear and how to make it happen.
- **Dark mode**: the tokens support it, but `index.html` pins `data-theme="light"`
  because modals and some components still hardcode light surfaces. Remove the
  attribute once those are migrated.
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
