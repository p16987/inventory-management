<template>
  <!-- Mobile-only trigger, fixed over the content column. -->
  <button
    ref="toggleRef"
    class="nav-toggle"
    type="button"
    :aria-expanded="String(drawerOpen)"
    aria-controls="app-sidebar"
    :aria-label="drawerOpen ? 'Close navigation' : 'Open navigation'"
    @click="toggleDrawer"
  >
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path v-if="!drawerOpen" d="M3 6h18M3 12h18M3 18h18" />
      <path v-else d="M6 6l12 12M18 6L6 18" />
    </svg>
  </button>

  <div
    class="sidebar-backdrop"
    :class="{ 'is-visible': drawerOpen }"
    aria-hidden="true"
    @click="closeDrawer"
  />

  <aside
    id="app-sidebar"
    ref="asideRef"
    class="sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-open': drawerOpen }"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
      <span v-show="!collapsed" class="brand-text">
        <span class="brand-name">{{ brand.name }}</span>
        <span v-if="brand.subtitle" class="brand-subtitle">{{ brand.subtitle }}</span>
      </span>
    </div>

    <nav class="sidebar-nav" aria-label="Main">
      <ul class="nav-list">
        <li v-for="item in items" :key="item.to">
          <router-link
            :to="item.to"
            class="nav-item"
            :class="{ 'is-active': isActive(item) }"
            :aria-current="isActive(item) ? 'page' : undefined"
            :title="collapsed ? item.label : undefined"
          >
            <span class="nav-icon" aria-hidden="true">
              <svg v-if="item.icon" viewBox="0 0 24 24"><path :d="item.icon" /></svg>
              <span v-else class="nav-monogram">{{ item.label.charAt(0) }}</span>
            </span>
            <!-- Kept in the DOM when collapsed so screen readers still read a
                 label; hidden visually rather than removed. -->
            <span class="nav-label" :class="{ 'sr-only': collapsed }">{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="sidebar-footer">
      <!-- App-level chrome (locale, account) lives here; per-page controls stay
           with the page. -->
      <slot name="footer" :collapsed="collapsed" />

      <button
        class="collapse-btn"
        type="button"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="toggleCollapse"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path :d="collapsed ? 'M9 6l6 6-6 6' : 'M15 6l-6 6 6 6'" />
        </svg>
        <span v-show="!collapsed" class="collapse-label">Collapse</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const STORAGE_KEY = 'sidebar:collapsed'

export default {
  name: 'AppSidebar',
  props: {
    // Built in App.vue from the router's own records, so a route added later
    // shows up without editing markup here.
    items: {
      type: Array,
      required: true
    },
    brand: {
      type: Object,
      default: () => ({ name: 'App', subtitle: '' })
    }
  },
  emits: ['update:collapsed'],
  setup(props, { emit }) {
    const route = useRoute()

    const collapsed = ref(false)
    const drawerOpen = ref(false)
    const isMobile = ref(false)
    const asideRef = ref(null)
    const toggleRef = ref(null)

    const brandInitial = computed(() => (props.brand.name || 'A').charAt(0).toUpperCase())

    // Prefix match, not equality: /orders/42 must keep "Orders" lit. '/' is the
    // exception, since every path starts with it. The trailing-slash check stops
    // /order matching /orders-archive.
    const isActive = (item) => {
      const current = route.path
      if (item.exact || item.to === '/') return current === item.to
      return current === item.to || current.startsWith(item.to + '/')
    }

    const toggleCollapse = () => {
      collapsed.value = !collapsed.value
      emit('update:collapsed', collapsed.value)
      // Storage throws in private mode and some webviews; a sidebar that can't
      // remember a preference is fine, one that crashes the app is not.
      try {
        localStorage.setItem(STORAGE_KEY, collapsed.value ? '1' : '0')
      } catch (err) {
        /* preference simply won't persist */
      }
    }

    const openDrawer = async () => {
      drawerOpen.value = true
      await nextTick()
      // Move focus into the drawer so keyboard and screen-reader users land
      // where the change happened instead of continuing behind the overlay.
      const first = asideRef.value && asideRef.value.querySelector('.nav-item')
      if (first) first.focus()
    }

    const closeDrawer = () => {
      if (!drawerOpen.value) return
      drawerOpen.value = false
      // Return focus to the control that opened it, or the next Tab restarts
      // from the top of the document.
      if (toggleRef.value) toggleRef.value.focus()
    }

    const toggleDrawer = () => {
      if (drawerOpen.value) closeDrawer()
      else openDrawer()
    }

    const onKeydown = (event) => {
      if (event.key === 'Escape') closeDrawer()
    }

    let mq = null
    const onMediaChange = (event) => {
      isMobile.value = event.matches
      if (!event.matches) drawerOpen.value = false
    }

    onMounted(() => {
      try {
        collapsed.value = localStorage.getItem(STORAGE_KEY) === '1'
      } catch (err) {
        /* default to expanded */
      }
      emit('update:collapsed', collapsed.value)

      // Keep this breakpoint in sync with the one in the styles below and in
      // App.vue; CSS custom properties can't be used inside media queries.
      mq = window.matchMedia('(max-width: 900px)')
      isMobile.value = mq.matches
      mq.addEventListener('change', onMediaChange)
      document.addEventListener('keydown', onKeydown)
    })

    onBeforeUnmount(() => {
      if (mq) mq.removeEventListener('change', onMediaChange)
      document.removeEventListener('keydown', onKeydown)
      document.body.style.removeProperty('overflow')
    })

    // Navigating is a completed action; leaving the drawer open over the page
    // the user just asked for is the classic mobile nav bug.
    watch(() => route.fullPath, closeDrawer)

    // Stop the page behind the drawer scrolling under the user's finger.
    watch(drawerOpen, (open) => {
      if (open && isMobile.value) document.body.style.overflow = 'hidden'
      else document.body.style.removeProperty('overflow')
    })

    return {
      collapsed,
      drawerOpen,
      asideRef,
      toggleRef,
      brandInitial,
      isActive,
      toggleCollapse,
      toggleDrawer,
      closeDrawer
    }
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
  width: var(--sidebar-width);
  height: 100vh;
  height: 100dvh;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  transition: width var(--duration-base) var(--ease),
    transform var(--duration-base) var(--ease);
}

.sidebar.is-collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: var(--topbar-height);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  overflow: hidden;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: var(--color-text-inverse);
  font-weight: var(--weight-bold);
  font-size: var(--text-sm);
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-tight);
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-3) var(--space-2);
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  margin-bottom: 2px;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  white-space: nowrap;
  transition: background-color var(--duration-fast) var(--ease),
    color var(--duration-fast) var(--ease);
}

.nav-item:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

/* Weight, colour AND a tinted surface. One signal alone is easy to miss when
   the rail is scanned peripherally. */
.nav-item.is-active {
  background: var(--color-accent-surface);
  color: var(--color-accent);
  font-weight: var(--weight-semibold);
}

.nav-item:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: -2px;
}

.nav-icon {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-icon svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.nav-monogram {
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
}

/* Japanese labels are longer than the English ones; truncate rather than wrap,
   which would break the row rhythm. */
.nav-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.is-collapsed .nav-item {
  justify-content: center;
  padding-inline: 0;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: var(--space-2);
  border-top: 1px solid var(--color-border);
}

.collapse-btn {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: var(--text-sm);
  cursor: pointer;
}

.collapse-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.collapse-btn svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.is-collapsed .collapse-btn {
  justify-content: center;
  padding-inline: 0;
}

.nav-toggle {
  display: none;
  position: fixed;
  top: var(--space-3);
  left: var(--space-3);
  z-index: var(--z-drawer);
  width: 40px;
  height: 40px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}

.nav-toggle svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}

.sidebar-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  z-index: calc(var(--z-drawer) - 1);
  background: rgba(2, 6, 23, 0.45);
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--duration-base) var(--ease);
}

@media (max-width: 900px) {
  .nav-toggle { display: grid; }

  .sidebar-backdrop { display: block; }
  .sidebar-backdrop.is-visible { opacity: 1; pointer-events: auto; }

  /* Off-canvas rather than squeezed: at phone width a 248px rail beside the
     content leaves no usable column for the content itself. */
  .sidebar {
    width: var(--sidebar-width);
    transform: translateX(-100%);
    box-shadow: var(--shadow-lg);
    z-index: var(--z-drawer);
  }

  .sidebar.is-open { transform: translateX(0); }

  /* Collapse is a desktop affordance; inside a drawer it only hides labels. */
  .sidebar.is-collapsed { width: var(--sidebar-width); }
  .sidebar.is-collapsed .nav-item {
    justify-content: flex-start;
    padding-inline: var(--space-3);
  }
  .collapse-btn { display: none; }

  .sidebar-brand { padding-left: calc(var(--space-4) + 44px); }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
