<template>
  <!-- Backdrop only exists while the mobile drawer is open -->
  <div v-if="!isDesktop && open" class="sidebar-backdrop" @click="$emit('close')" />
  <aside
    id="app-sidebar"
    class="sidebar"
    :class="{ collapsed: isDesktop && collapsed, drawer: !isDesktop, 'drawer-open': !isDesktop && open }"
  >
    <div class="sidebar-brand">
      <div class="brand-mark" aria-hidden="true">{{ brandInitial }}</div>
      <div v-if="!(isDesktop && collapsed)" class="brand-text">
        <span class="brand-name">{{ brandName }}</span>
        <span v-if="brandSubtitle" class="brand-subtitle">{{ brandSubtitle }}</span>
      </div>
    </div>

    <nav class="sidebar-nav" :aria-label="navLabel">
      <section v-for="group in groups" :key="group.label" class="nav-group" :aria-label="group.label">
        <h2 class="nav-group-label">{{ group.label }}</h2>
        <ul>
          <li v-for="item in group.items" :key="item.to">
            <router-link
              :to="item.to"
              class="nav-link"
              :aria-label="item.label"
              :data-tip="item.label"
              exact-active-class="active"
              @click="$emit('close')"
            >
              <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path v-for="d in icons[item.icon]" :key="d" :d="d" />
              </svg>
              <span class="nav-label">{{ item.label }}</span>
            </router-link>
          </li>
        </ul>
      </section>
    </nav>

    <div v-if="isDesktop" class="sidebar-footer">
      <button
        class="collapse-btn"
        type="button"
        :aria-expanded="!collapsed"
        :aria-label="collapsed ? expandLabel : collapseLabel"
        @click="$emit('toggle-collapse')"
      >
        <svg class="nav-icon" :class="{ flipped: collapsed }" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path v-for="d in icons.chevronsLeft" :key="d" :d="d" />
        </svg>
        <span class="nav-label">{{ collapseLabel }}</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { icons } from '../utils/icons'

// Presentational sidebar: the parent owns state and passes already-translated labels.
export default {
  name: 'AppSidebar',
  props: {
    groups: { type: Array, required: true },
    collapsed: { type: Boolean, default: false },
    open: { type: Boolean, default: false },
    isDesktop: { type: Boolean, default: true },
    brandName: { type: String, default: '' },
    brandSubtitle: { type: String, default: '' },
    brandInitial: { type: String, default: '' },
    navLabel: { type: String, default: 'Main navigation' },
    collapseLabel: { type: String, default: 'Collapse sidebar' },
    expandLabel: { type: String, default: 'Expand sidebar' }
  },
  emits: ['toggle-collapse', 'close'],
  setup() {
    return { icons }
  }
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-w);
  height: 100dvh;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  z-index: var(--z-sidebar);
  transition: width var(--transition);
}
.sidebar.collapsed { width: var(--sidebar-w-collapsed); }

/* Mobile drawer: off-canvas until opened */
.sidebar.drawer {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: var(--z-drawer);
  max-width: 85vw;
  transform: translateX(-100%);
  /* visibility removes the off-canvas links from the tab order once the slide-out finishes */
  visibility: hidden;
  transition: transform var(--transition), visibility 0s linear var(--transition);
  box-shadow: var(--shadow-lg);
}
.sidebar.drawer-open {
  transform: translateX(0);
  visibility: visible;
  transition: transform var(--transition), visibility 0s;
}
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  z-index: calc(var(--z-drawer) - 1);
}

.sidebar-brand {
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-5);
  border-bottom: 1px solid var(--border);
}
.brand-mark {
  width: 32px; height: 32px;
  flex-shrink: 0;
  display: grid; place-items: center;
  background: var(--primary); color: var(--surface);
  border-radius: var(--radius-md);
  font-weight: 700;
}
.brand-text { display: flex; flex-direction: column; min-width: 0; line-height: 1.2; }
.brand-name { font-weight: 700; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.brand-subtitle { font-size: var(--text-xs); color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-nav { flex: 1; overflow-y: auto; padding: var(--space-4) var(--space-3); }
.nav-group + .nav-group { margin-top: var(--space-5); }
.nav-group ul { list-style: none; display: flex; flex-direction: column; gap: var(--space-1); }
.nav-group-label {
  padding: 0 var(--space-3) var(--space-2);
  font-size: var(--text-xs); font-weight: 600;
  letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--text-muted);
}
.collapsed .nav-group-label { font-size: 0; height: 1px; padding: 0; margin: 0 var(--space-3) var(--space-2); background: var(--border); }

.nav-link, .collapse-btn {
  position: relative;
  display: flex; align-items: center; gap: var(--space-3);
  width: 100%; height: 40px;
  padding: 0 var(--space-3);
  border: 0; background: transparent;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font: inherit; font-weight: 500;
  text-decoration: none; cursor: pointer;
  transition: background var(--transition), color var(--transition);
}
.nav-link:hover, .collapse-btn:hover { background: var(--surface-hover); color: var(--text); }
.nav-link.active { background: var(--primary-soft); color: var(--primary); font-weight: 600; }
.nav-link.active::before {
  content: ''; position: absolute; left: calc(-1 * var(--space-3));
  top: 8px; bottom: 8px; width: 3px;
  background: var(--primary); border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
.nav-icon { width: 20px; height: 20px; flex-shrink: 0; transition: transform var(--transition); }
.nav-icon.flipped { transform: rotate(180deg); }
.nav-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Collapsed rail: icons only, label shown as a tooltip.
   overflow must be visible here or the nav's scroll container clips the tooltip. */
.collapsed .sidebar-nav { overflow: visible; }
.collapsed .nav-label { display: none; }
.collapsed .nav-link, .collapsed .collapse-btn { justify-content: center; padding: 0; }
.collapsed .nav-link:hover::after,
.collapsed .nav-link:focus-visible::after {
  content: attr(data-tip);
  position: absolute; left: calc(100% + var(--space-2)); top: 50%; transform: translateY(-50%);
  padding: var(--space-1) var(--space-2);
  background: var(--text); color: var(--surface);
  font-size: var(--text-xs); white-space: nowrap;
  border-radius: var(--radius-sm); z-index: var(--z-toast); pointer-events: none;
}

.sidebar-footer { padding: var(--space-3); border-top: 1px solid var(--border); }
</style>
