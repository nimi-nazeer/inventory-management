# Sidebar and shell spec

## Structure

```
.app-shell (display:flex, height:100dvh)
├── AppSidebar (fixed width, full height, own scroll)
│   ├── brand (logo/mark + app name + subtitle)
│   ├── nav (grouped sections)
│   └── footer (collapse toggle)
└── .app-main (flex:1, min-width:0, column)
    ├── AppTopbar (sticky, height var(--topbar-h))
    └── .app-content (overflow:auto, padding var(--space-6), inner max-width var(--content-max))
```

The shell scrolls inside `.app-content`, not the body, so the sidebar and topbar never move. If a view relied on `window` scroll (scroll listeners, `scrollTo`), update it to the content container.

## Dimensions and states

- Expanded 256px; collapsed 72px (icons only). Animate `width` ~200ms ease; honor `prefers-reduced-motion` (no transition).
- Nav item: height 40px, radius `--radius-md`, icon 20px + label, gap `--space-3`, padding `0 --space-3`.
- States: default (muted text), hover (`--surface-hover`), active (`--primary-soft` bg + `--primary` text + 2-3px left indicator), focus-visible (2px ring, offset 2px). The active item comes from `router-link-active` / `aria-current="page"`; use exact matching for `/` so Overview is not always active.
- Section labels: uppercase, `--text-xs`, muted, hidden when collapsed (replace with a thin divider).
- Collapsed: show the label as a tooltip on hover/focus (CSS `:hover`/`:focus-visible` pseudo tooltip is enough) and keep `aria-label` on each link so screen readers still get names.
- Persist collapsed state in `localStorage` (wrap in try/catch); default expanded on desktop.

## Responsive

- `>= 1024px`: persistent sidebar, collapsible.
- `< 1024px`: sidebar becomes an off-canvas drawer (transform translateX, fixed, `--z-drawer`) with a backdrop (`--z-drawer` minus one). A hamburger button appears at the left of the topbar. Close on: backdrop click, Escape, route change, nav link click.
- Drawer is always full-width labels (never the collapsed rail).
- Topbar utilities collapse gracefully: hide the app title text first, keep the profile menu; page-level filters wrap or move into a horizontally scrollable row below the title rather than overflowing.
- Detect breakpoint with `window.matchMedia('(min-width: 1024px)')` and a listener, not by reading `innerWidth` on every render. Remove the listener on unmount.

## Accessibility

- `<aside>` with `<nav aria-label="Main">`; each group is a list (`ul/li`) with a labelled heading.
- Collapse toggle: `<button aria-expanded>` with a text/aria label ("Collapse sidebar" / "Expand sidebar").
- Hamburger: `aria-controls` pointing at the sidebar id, `aria-expanded` reflecting drawer state.
- When the drawer opens, move focus into it; on close, return focus to the hamburger. Trap focus only if easy; at minimum Escape must close.
- Color contrast: muted text on surface must be >= 4.5:1; the active state must not rely on color alone (the left indicator and weight cover this).

## Topbar

- Left: hamburger (mobile) + page title (`--text-xl`, weight 600) derived from the active nav item's label, via route `meta.title` or a lookup from the nav config. Do not duplicate by also adding an `h1` in each view; either the topbar owns the title or views do. Pick one and remove the other.
- Center/below: slot for page-level controls (e.g. existing filter bar). Reuse the component, restyle only its container, so filter logic is untouched.
- Right: existing utility components (language switcher, profile menu). Menus open downward and align right; verify they are not clipped by `overflow` on the topbar.

## Page header and content

Each view starts with a consistent header block: optional eyebrow/breadcrumb, description in muted text, and actions aligned right. Vertical rhythm between page sections is `--space-6`; card grids use `gap: var(--space-5)`.
