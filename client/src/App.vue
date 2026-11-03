<template>
  <div class="app-shell">
    <AppSidebar
      :groups="navGroups"
      :collapsed="collapsed"
      :open="drawerOpen"
      :is-desktop="isDesktop"
      :brand-name="t('nav.companyName')"
      :brand-subtitle="t('nav.subtitle')"
      :brand-initial="brandInitial"
      :nav-label="t('nav.mainNavigation')"
      :collapse-label="t('nav.collapseSidebar')"
      :expand-label="t('nav.expandSidebar')"
      @toggle-collapse="toggleCollapse"
      @close="drawerOpen = false"
    />

    <div class="app-main">
      <AppTopbar
        :title="pageTitle"
        :is-desktop="isDesktop"
        :drawer-open="drawerOpen"
        :menu-label="t('nav.openMenu')"
        @open-menu="drawerOpen = true"
      >
        <template #actions>
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </template>
        <FilterBar />
      </AppTopbar>

      <!-- The shell scrolls here (not the window) so sidebar and topbar stay fixed -->
      <main class="app-content">
        <div class="app-content-inner">
          <router-view />
        </div>
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import AppSidebar from './components/AppSidebar.vue'
import AppTopbar from './components/AppTopbar.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    AppSidebar,
    AppTopbar
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    const route = useRoute()

    // ---- App shell: navigation, sidebar state, page title ----

    // Nav config. Labels are translated here so the sidebar stays presentational.
    // Groups: Overview / Operations / Finance (see sidebar spec).
    const navGroups = computed(() => [
      {
        label: t('nav.groupOverview'),
        items: [{ to: '/', label: t('nav.overview'), icon: 'dashboard' }]
      },
      {
        label: t('nav.groupOperations'),
        items: [
          { to: '/inventory', label: t('nav.inventory'), icon: 'inventory' },
          { to: '/orders', label: t('nav.orders'), icon: 'orders' },
          { to: '/restocking', label: t('nav.restocking'), icon: 'restocking' },
          { to: '/demand', label: t('nav.demandForecast'), icon: 'forecast' }
        ]
      },
      {
        label: t('nav.groupFinance'),
        items: [
          { to: '/spending', label: t('nav.finance'), icon: 'finance' },
          { to: '/reports', label: t('nav.reports'), icon: 'reports' }
        ]
      }
    ])

    // The topbar owns the page title; derive it from the active nav item
    const pageTitle = computed(() => {
      for (const group of navGroups.value) {
        const item = group.items.find(i => i.to === route.path)
        if (item) return item.label
      }
      return t('nav.companyName')
    })

    const brandInitial = computed(() => t('nav.companyName').charAt(0).toUpperCase())

    // Collapsed rail preference persists across reloads (storage can throw in private mode)
    const COLLAPSE_KEY = 'sidebar-collapsed'
    const readCollapsed = () => {
      try {
        return localStorage.getItem(COLLAPSE_KEY) === 'true'
      } catch (err) {
        return false
      }
    }
    const collapsed = ref(readCollapsed())
    const toggleCollapse = () => {
      collapsed.value = !collapsed.value
      try {
        localStorage.setItem(COLLAPSE_KEY, String(collapsed.value))
      } catch (err) {
        // Preference just won't persist
      }
    }

    // >= 1024px: persistent sidebar; below: off-canvas drawer. matchMedia listener, not innerWidth.
    const desktopQuery = window.matchMedia('(min-width: 1024px)')
    const isDesktop = ref(desktopQuery.matches)
    const drawerOpen = ref(false)
    const onBreakpointChange = (e) => {
      isDesktop.value = e.matches
      if (e.matches) drawerOpen.value = false
    }

    // Close the drawer on route change (covers nav link clicks too)
    watch(() => route.path, () => {
      drawerOpen.value = false
    })

    // Move focus into the drawer when it opens; return it to the hamburger when it closes
    watch(drawerOpen, async (open, wasOpen) => {
      await nextTick()
      if (open) {
        const first = document.querySelector('#app-sidebar .nav-link')
        if (first) first.focus()
      } else if (wasOpen) {
        const burger = document.querySelector('.menu-btn')
        if (burger) burger.focus()
      }
    })

    const onKeydown = (e) => {
      if (e.key === 'Escape' && drawerOpen.value) drawerOpen.value = false
    }

    onMounted(() => {
      desktopQuery.addEventListener('change', onBreakpointChange)
      window.addEventListener('keydown', onKeydown)
    })
    onBeforeUnmount(() => {
      desktopQuery.removeEventListener('change', onBreakpointChange)
      window.removeEventListener('keydown', onKeydown)
    })

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      navGroups,
      pageTitle,
      brandInitial,
      collapsed,
      toggleCollapse,
      isDesktop,
      drawerOpen,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* Resets, body font and design tokens live in styles/tokens.css (imported in main.js). */

/* ---- App shell ---- */
.app-shell {
  display: flex;
  height: 100dvh;
  overflow: hidden;
}

.app-main {
  flex: 1;
  min-width: 0; /* lets wide tables and charts shrink instead of pushing the layout */
  display: flex;
  flex-direction: column;
}

.app-content {
  flex: 1;
  overflow: auto;
  padding: var(--space-6);
}

.app-content-inner {
  max-width: var(--content-max);
  margin: 0 auto;
}

@media (max-width: 1023px) {
  .app-content {
    padding: var(--space-4);
  }
}

/* ---- Shared page building blocks (used by every view) ---- */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-xs);
  transition: border-color var(--transition), box-shadow var(--transition);
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: var(--warning); }
.stat-card.success .stat-value { color: var(--success); }
.stat-card.danger .stat-value { color: var(--danger); }
.stat-card.info .stat-value { color: var(--info); }

.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--bg);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: #475569; /* slate-600: table header text, between --text-secondary and --text-muted */
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--surface-hover);
  color: var(--text-secondary);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color var(--transition);
}

tbody tr:hover {
  background: var(--bg);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success,
.badge.increasing {
  background: var(--success-bg);
  color: var(--success-text);
}

.badge.warning,
.badge.medium {
  background: var(--warning-bg);
  color: var(--warning-text);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--danger-bg);
  color: var(--danger-text);
}

.badge.info,
.badge.low {
  background: var(--info-bg);
  color: var(--info-text);
}

/* Indigo "stable" trend badge has no status token; kept as a deliberate one-off */
.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.loading {
  text-align: center;
  padding: var(--space-9);
  color: var(--text-muted);
  font-size: var(--text-base);
}

.error {
  background: var(--danger-bg);
  border: 1px solid var(--danger-bg);
  color: var(--danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
