<template>
  <div class="app-shell">
    <!-- Keyboard users shouldn't tab through the whole rail on every page. -->
    <a class="skip-link" href="#main">Skip to content</a>

    <AppSidebar
      :items="navItems"
      :brand="{ name: t('nav.companyName'), subtitle: t('nav.subtitle') }"
      @update:collapsed="sidebarCollapsed = $event"
    >
      <!-- App-level chrome that used to sit in the top bar. It's set once and
           then forgotten, so it belongs at the bottom of the rail rather than
           in prime horizontal space. -->
      <template #footer>
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </template>
    </AppSidebar>

    <div class="app-main" :class="{ 'is-narrow': sidebarCollapsed }">
      <!-- Filters change what you're looking at rather than where you are, so
           they stay with the content column instead of moving into the nav. -->
      <FilterBar class="app-filters" />
      <main id="main" class="app-content">
        <router-view />
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import AppSidebar from './components/AppSidebar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const router = useRouter()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const sidebarCollapsed = ref(false)
    const apiTasks = ref([])

    // Nav is derived from the router's own records rather than hand-written
    // markup, so adding a route with meta.nav is all it takes to appear in the
    // sidebar. t() reads a module-level ref, which makes this recompute when
    // the locale changes.
    const navItems = computed(() =>
      router
        .getRoutes()
        .filter((r) => r.meta && r.meta.nav)
        .sort((a, b) => (a.meta.nav.order || 0) - (b.meta.nav.order || 0))
        .map((r) => ({
          to: r.path,
          label: r.meta.nav.labelKey ? t(r.meta.nav.labelKey) : r.meta.nav.label,
          icon: r.meta.nav.icon,
          exact: r.path === '/'
        }))
    )

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
      navItems,
      sidebarCollapsed,
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
/* Global, unscoped: this file owns the page frame. Everything else — cards,
   tables, badges, buttons, states — now lives in styles/primitives.css, built
   on styles/tokens.css. If you need a value that isn't a token, add it to the
   token file rather than inlining it here. */

/* The app's original reset. Kept deliberately: views rely on headings and
   paragraphs having no default margin, and removing it would re-space every
   screen at once. */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-shell {
  min-height: 100vh;
  background: var(--color-bg);
}

/* The sidebar is fixed, so the content column is offset with margin rather than
   being a scroll container of its own. A scroll container would break
   `position: sticky` inside views — which is how sticky table headers quietly
   stop working. */
.app-main {
  margin-left: var(--sidebar-width);
  min-width: 0;
  transition: margin-left var(--duration-base) var(--ease);
}

.app-main.is-narrow {
  margin-left: var(--sidebar-width-collapsed);
}

.app-filters {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
}

.app-content {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--content-pad-y) var(--content-pad-x);
}

.skip-link {
  position: absolute;
  left: var(--space-4);
  top: -48px;
  z-index: var(--z-toast);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  text-decoration: none;
  transition: top var(--duration-fast) var(--ease);
}

.skip-link:focus {
  top: var(--space-3);
}

/* Keep this breakpoint in sync with AppSidebar.vue; CSS custom properties
   can't be used inside media queries. */
@media (max-width: 900px) {
  /* The drawer overlays the page instead of displacing it, and the menu button
     needs room beside the filter row. */
  .app-main,
  .app-main.is-narrow {
    margin-left: 0;
  }

  .app-filters {
    padding-left: calc(var(--space-4) + 52px);
  }
}

/* --- Migration shims -------------------------------------------------------
   Views still use bare <table> markup and the old .loading / .error classes.
   These map them onto the primitives so every screen keeps working while views
   are migrated one at a time. Delete each shim once no view depends on it —
   `grep -rn "class=\"loading\"" src/` will tell you. */

.app-content table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.app-content thead th {
  background: var(--color-surface-sunken);
  text-align: left;
  padding: var(--cell-pad-y) var(--cell-pad-x);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--color-text-muted);
  white-space: nowrap;
  border-bottom: 1px solid var(--color-border);
}

.app-content tbody td {
  padding: var(--cell-pad-y) var(--cell-pad-x);
  height: var(--row-height);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-body);
}

.app-content tbody tr {
  transition: background-color var(--duration-fast) var(--ease);
}

.app-content tbody tr:hover {
  background: var(--color-surface-hover);
}

.loading {
  padding: var(--space-12) var(--space-6);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.error {
  padding: var(--space-4);
  margin: var(--space-4) 0;
  border-radius: var(--radius-md);
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  color: var(--danger-fg);
  font-size: var(--text-sm);
}
</style>
