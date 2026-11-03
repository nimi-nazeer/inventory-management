---
name: vue-saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface - a vertical left sidebar instead of a top nav bar, a slim top utility bar, design tokens for consistent spacing/radius/shadow/type, and a polished professional look. Use this skill whenever the user wants to restyle, modernize, or "make professional" a Vue app, move navigation from the top to a side/left/vertical nav, add a collapsible sidebar or mobile drawer, introduce a design system or CSS variables, or unify inconsistent spacing across views, even if they never say "SaaS" or "sidebar" explicitly.
---

# Vue 3 SaaS Redesign

Turn a Vue 3 app with a horizontal top nav into an app-shell layout: left sidebar for navigation, a slim top bar for page context and utilities, and a content area whose spacing comes from shared tokens. The goal is that the app *looks designed*, not merely rearranged, and that nothing functional breaks along the way.

Two principles drive every decision below:

1. **Behavior is frozen, presentation is not.** Routes, API calls, props, emitted events, i18n keys and store logic stay as they are. Redesigns that "also fix a few things" are impossible to review and tend to break filters or data flow. Only touch templates and styles, plus the new shell components.
2. **Preserve the app's identity, formalize it.** Projects usually already have a palette, type choices and conventions (check `CLAUDE.md`, `README`, global CSS). Extract those into tokens rather than inventing a new look. A consistent app beats a trendy one.

## Workflow

### 1. Audit (read before writing)

Collect these facts first; they determine everything else:

- **Routes and nav items**: read the router (`main.js` / `router/index.js`). Each nav entry needs a route, a label, and an icon.
- **Current shell**: the file that renders the top nav (usually `App.vue`) and every component it mounts (filter bars, profile menu, language switcher, modals).
- **Conventions to honor**: `CLAUDE.md` / `client/CLAUDE.md` rules such as "no emojis in UI", palette, "delegate `.vue` edits to subagent X", component API style (Options API with `setup()` vs `<script setup>`). Follow them; they are the user's standing instructions.
- **i18n**: if a translation composable exists, every new visible string (section labels, "Collapse", "Open menu") needs a key in *every* locale file.
- **Hardcoded values**: grep the styles for the distinct colors, paddings, radii and shadows in use. This tells you which tokens to define and how messy the normalization pass will be.
- **Layout-sensitive code**: `position: sticky`, `100vh`, `z-index`, `Teleport`ed modals, and charts that measure their container. Moving to a sidebar layout changes the available width and sticky offsets, so these are where regressions hide.

Summarize the audit to the user in a few lines (nav items found, conventions, risk spots) before making changes.

### 2. Define tokens

Copy `assets/tokens.css` into the project's styles location (e.g. `src/styles/tokens.css`) and import it once in the entry file before other styles. Then **edit the color tokens to match the project's existing palette** - the template uses slate defaults, which suit most apps but are only a starting point. See `references/design-tokens.md` for the scale rationale and how to map existing values.

Why tokens first: spacing and radius consistency comes from having a small set of allowed values. If you restyle views before the tokens exist, you will hardcode new magic numbers.

### 3. Build the shell

Create three pieces (templates in `assets/`; adapt to the project's component style and naming):

- `AppSidebar` - brand, grouped nav links, collapse toggle. See `references/sidebar-spec.md` for dimensions, states and accessibility requirements. Do not skip the spec's a11y and mobile sections; a sidebar that only works with a mouse on a wide monitor is half done.
- `AppTopbar` - page title (derived from the current route's nav label), a slot for page-level controls such as the existing filter bar, and the utility cluster (language switcher, profile menu) that used to sit in the top nav. Move the existing components; do not rewrite them.
- Shell layout in `App.vue`: sidebar + (topbar over scrollable main). Keep existing modals and their handlers where they are.

The templates are starting points, not drop-ins: copy them into the project (components to `src/components/`, `icons.js` to e.g. `src/utils/`), then fix the import paths, rename to match local conventions, and port `<script setup>` to `setup()` if the project uses Options API.

Shell wiring in `App.vue` (the parent owns state and translations, so the sidebar stays presentational):

```vue
<div class="app-shell">
  <AppSidebar :groups="navGroups" :collapsed="collapsed" :open="drawerOpen" :is-desktop="isDesktop"
              @toggle-collapse="toggleCollapse" @close="drawerOpen = false" />
  <div class="app-main">
    <AppTopbar :title="pageTitle" :is-desktop="isDesktop" :drawer-open="drawerOpen" @open-menu="drawerOpen = true">
      <template #actions><!-- existing LanguageSwitcher + ProfileMenu --></template>
      <!-- existing filter bar, if any --> 
    </AppTopbar>
    <main class="app-content"><router-view /></main>
  </div>
</div>
```

`navGroups` is a computed built from translated labels; `pageTitle` is looked up from the current route in that same structure. Persist `collapsed`, track `isDesktop` with `matchMedia`, and close the drawer on route change and Escape (see the spec).

Nav icons: use inline SVG (the template `assets/icons.js` has stroke-style paths). Do not add an icon dependency unless the user agrees, and do not use emoji.

Group nav items into sections when there are more than ~5 (e.g. Overview / Operations / Finance), inferring groups from the route names. Grouping is what makes a sidebar scan quickly.

### 4. Normalize the pages

Walk through each view and shared component and apply tokens. Work in small passes so a visual regression can be traced to one change:

1. Page container: remove per-view outer `max-width`/padding that fights the shell; give pages a consistent page header (title + optional actions) and vertical rhythm using `--space-*`.
2. Cards/panels: one surface style (`--surface`, `--border`, `--radius-lg`, `--shadow-sm`, `--space-5` padding).
3. Replace hardcoded padding/margin/gap/radius/shadow/font-size with the nearest token. Round to the nearest scale step; do not add new steps to match odd values - the point is to converge.
4. Tables, form controls, buttons, badges: consistent heights (`--control-h`), focus rings, hover states, status colors from tokens.
5. Large files (1000+ lines) get the same mechanical treatment; avoid restructuring their templates beyond what the shell requires.

If the project's rules require delegating `.vue` edits to a specialist subagent, delegate each pass with a precise brief (files, tokens file path, spec section) instead of editing directly.

### 5. Verify

A redesign is only done when you have seen it:

- Run the production build (`npm run build`) - it catches template/import errors quickly.
- Load the app in a browser (Playwright MCP if configured, otherwise the dev server plus screenshots) and check **every route** at three widths: ~1440px, ~1024px, ~390px. Look at: sidebar active state, collapse/expand, mobile drawer open/close, topbar overflow, sticky elements sitting at the right offset, charts/tables not clipped or overflowing horizontally, modals above the sidebar.
- Check that existing behavior still works: change a filter, switch language, open the profile menu and modals.
- Check the console for new warnings.

Report what you verified and anything you could not (for example, no browser available).

## Output expectations

Finish with a short summary: new files, files modified, tokens introduced, the nav groups chosen, and any places where you deliberately left old styles alone and why. Mention follow-ups (dark mode, remaining unmigrated styles) without doing them unasked.

## Pitfalls that recur

- **Flex/grid children overflowing**: the content column needs `min-width: 0`, otherwise wide tables and charts push the layout past the viewport.
- **Sticky offsets**: anything that was `top: 70px` under the old nav now belongs under the topbar (`var(--topbar-h)`) or should just be `top: 0` inside the scroll container.
- **`100vh` on mobile**: use `100dvh` for the shell so browser chrome does not clip the bottom of the sidebar.
- **Z-index**: use the `--z-*` scale; modals must stay above the sidebar and the drawer backdrop.
- **Charts after collapse**: if charts size themselves from container width, the sidebar transition can leave them stale. Check, and trigger a resize on `transitionend` if needed.
- **Global CSS reset vs scoped styles**: keep global styles in one place (tokens + base); do not scatter new globals into views.
- **Locale files**: adding a string to `en` only leaves other languages showing raw keys.
