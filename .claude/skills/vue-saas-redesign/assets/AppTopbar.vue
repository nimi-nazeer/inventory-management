<!--
  AppTopbar - starter template. Owns the page title; remove per-view h1s that duplicate it.
  The default slot is for page-level controls (e.g. the existing filter bar);
  the "actions" slot is for the utility cluster (language switcher, profile menu).
  Reuse the project's existing components in those slots - do not rewrite them.
-->
<template>
  <header class="topbar">
    <div class="topbar-row">
      <button
        v-if="!isDesktop"
        class="menu-btn"
        type="button"
        aria-controls="app-sidebar"
        :aria-expanded="drawerOpen"
        :aria-label="menuLabel"
        @click="$emit('open-menu')"
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor"
             stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
          <path v-for="d in icons.menu" :key="d" :d="d" />
        </svg>
      </button>

      <h1 class="page-title">{{ title }}</h1>

      <div class="topbar-actions">
        <slot name="actions" />
      </div>
    </div>

    <div v-if="$slots.default" class="topbar-controls">
      <slot />
    </div>
  </header>
</template>

<script setup>
import { icons } from '../assets/icons'

defineProps({
  title: { type: String, default: '' },
  isDesktop: { type: Boolean, default: true },
  drawerOpen: { type: Boolean, default: false },
  menuLabel: { type: String, default: 'Open menu' }
})
defineEmits(['open-menu'])
</script>

<style scoped>
.topbar {
  position: sticky; top: 0;
  z-index: var(--z-topbar);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.topbar-row {
  min-height: var(--topbar-h);
  display: flex; align-items: center; gap: var(--space-4);
  padding: 0 var(--space-6);
}
.page-title {
  font-size: var(--text-xl); font-weight: 600; letter-spacing: -0.01em;
  color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.topbar-actions { margin-left: auto; display: flex; align-items: center; gap: var(--space-3); }
.topbar-controls { padding: 0 var(--space-6) var(--space-4); }

.menu-btn {
  width: var(--control-h); height: var(--control-h);
  display: grid; place-items: center;
  border: 1px solid var(--border); background: var(--surface);
  border-radius: var(--radius-md); color: var(--text-secondary); cursor: pointer;
}
.menu-btn:hover { background: var(--surface-hover); }

@media (max-width: 1023px) {
  .topbar-row, .topbar-controls { padding-left: var(--space-4); padding-right: var(--space-4); }
}
</style>
