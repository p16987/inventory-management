import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

// Imported before App.vue on purpose: Vite injects a component's styles when
// the component is imported, so importing App first would let its styles
// outrank the global sheets on equal-specificity rules.
import './styles/tokens.css'
import './styles/primitives.css'

import App from './App.vue'
import { ICONS } from './icons'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Restocking from './views/Restocking.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'

// meta.nav is what the sidebar renders. Keeping the label on the route means a
// route added later can't be missing from the nav, and a nav entry can't point
// at a path that doesn't resolve. labelKey goes through i18n; a route with no
// meta.nav simply doesn't appear in the sidebar.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard,
      meta: { nav: { labelKey: 'nav.overview', icon: ICONS.overview, order: 1 } } },
    { path: '/inventory', component: Inventory,
      meta: { nav: { labelKey: 'nav.inventory', icon: ICONS.inventory, order: 2 } } },
    { path: '/orders', component: Orders,
      meta: { nav: { labelKey: 'nav.orders', icon: ICONS.orders, order: 3 } } },
    { path: '/restocking', component: Restocking,
      meta: { nav: { labelKey: 'nav.restocking', icon: ICONS.restocking, order: 4 } } },
    { path: '/demand', component: Demand,
      meta: { nav: { labelKey: 'nav.demandForecast', icon: ICONS.demand, order: 6 } } },
    { path: '/spending', component: Spending,
      meta: { nav: { labelKey: 'nav.finance', icon: ICONS.finance, order: 5 } } },
    { path: '/reports', component: Reports,
      meta: { nav: { labelKey: 'nav.reports', icon: ICONS.reports, order: 7 } } }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
