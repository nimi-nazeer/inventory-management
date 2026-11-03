# Design tokens

The tokens live in `assets/tokens.css` as CSS custom properties on `:root`. They are plain CSS, so they work with scoped styles, any component API style, and no build plugin.

## Scales and why

| Group | Values | Rationale |
|---|---|---|
| Spacing `--space-1..10` | 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 px | A 4px base grid. Few steps means two developers pick the same value for the same job. |
| Radius `--radius-sm/md/lg/xl/full` | 6, 8, 12, 16, 9999 | Controls use `md`, cards `lg`, modals `xl`, pills/avatars `full`. |
| Shadow `--shadow-xs/sm/md/lg` | soft, low-opacity, slate-tinted | Cards `sm`, popovers/menus `md`, modals `lg`. Avoid stacking shadow and heavy borders. |
| Type `--text-xs..3xl` | 12, 13, 14, 16, 18, 20, 24, 30 px | Body is 14px for dense data UIs. Page titles 24px, section titles 16-18px. |
| Layout | `--sidebar-w` 256px, `--sidebar-w-collapsed` 72px, `--topbar-h` 64px, `--content-max` 1440px | Referenced by the shell and by anything sticky. |
| Z-index `--z-*` | base, sticky, sidebar, topbar, drawer, modal, toast | One ordering, no ad-hoc `z-index: 9999`. |

## Mapping an existing palette

1. Grep for hex/rgb values used in styles and rank by frequency.
2. Assign the most-used dark text color to `--text`, mid gray to `--text-muted`, border gray to `--border`, page background to `--bg`, card white to `--surface`.
3. Keep the project's status colors (success/info/warning/danger) and define a tinted background for each (`--success-bg`) for badges.
4. Pick the single accent used for links/active states as `--primary`; derive `--primary-soft` (a ~10% tint) for active nav backgrounds.
5. Leave one-off chart colors alone unless they duplicate a token; charts often have meaningful, deliberate colors.

Example (from a slate-based app): text `#0f172a`, muted `#64748b`, border `#e2e8f0`, bg `#f8fafc` - these are the template defaults, so no edit is needed for such projects.

## Mapping spacing values

Round to the nearest step, preferring the smaller one on a tie:

`2-6px -> --space-1/2`, `10-14px -> --space-3`, `18-22px -> --space-5`, `28-36px -> --space-7`.

`rem` values: the template assumes 16px root. `0.75rem = 12px = --space-3`, `1.5rem = 24px = --space-6`, `2rem = 32px = --space-7`.

Leave sub-4px values (1-2px borders, hairlines) as they are.

## Dark mode

Tokens are structured as semantic names (`--surface`, `--text`) so dark mode later is a `[data-theme="dark"]` override of color tokens only. Do not implement it unless asked, but do not hardcode colors in new components, or it becomes expensive later.
