<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t('orders.title') }}</h2>
      <p>{{ t('orders.description') }}</p>
    </div>

    <!-- Skeletons are sized to the real table rows so the page doesn't jump when
         the data lands. The loading string stays for screen readers. -->
    <div v-if="loading" class="card" aria-busy="true">
      <span class="sr-only">{{ t('common.loading') }}</span>
      <div v-for="n in 6" :key="n" class="skeleton skeleton-row"></div>
    </div>
    <div v-else-if="error" class="state state--error">
      <p class="state-title">{{ error }}</p>
    </div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('status.delivered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Delivered').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('status.shipped') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Shipped').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('status.processing') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Processing').length }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t('status.backordered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Backordered').length }}</div>
        </div>
      </div>

      <!-- Restock orders submitted from the Restocking tab. English/USD by design. -->
      <div v-if="restockError" class="state state--error">
        <p class="state-title">{{ restockError }}</p>
      </div>
      <div v-else-if="restockOrders.length > 0" class="card">
        <div class="card-header">
          <h3 class="card-title">Submitted Orders ({{ restockOrders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="data-table restock-orders-table">
            <thead>
              <tr>
                <th class="col-order-number">Order Number</th>
                <th class="col-date">Created</th>
                <th class="col-items">Items</th>
                <th class="col-value num">Total Cost (USD)</th>
                <th class="col-lead num">Lead Time (Days)</th>
                <th class="col-date">Expected Delivery</th>
                <th class="col-status">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="restockOrder in restockOrders" :key="restockOrder.id">
                <td class="col-order-number"><strong>{{ restockOrder.order_number }}</strong></td>
                <td class="col-date">{{ formatRestockDate(restockOrder.created_date) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ restockOrder.items.length }} {{ restockOrder.items.length === 1 ? 'item' : 'items' }}
                    </summary>
                    <div class="items-dropdown restock-dropdown">
                      <div
                        v-for="line in restockOrder.items"
                        :key="line.item_sku"
                        class="item-entry"
                      >
                        <span class="item-name">{{ line.item_sku }} &mdash; {{ line.item_name }}</span>
                        <span class="item-meta">
                          Qty: {{ line.quantity }} @ {{ formatUsdExact(line.unit_cost) }}
                          &middot; Line total: {{ formatUsdExact(line.line_total) }}
                          &middot; Lead time: {{ line.lead_time_days }} days
                        </span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-value num"><strong>{{ formatUsdExact(restockOrder.total_cost) }}</strong></td>
                <td class="col-lead num">{{ restockOrder.lead_time_days }}</td>
                <td class="col-date">{{ formatRestockDate(restockOrder.expected_delivery) }}</td>
                <td class="col-status">
                  <span class="badge info">{{ restockOrder.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('orders.allOrders') }} ({{ orders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="data-table orders-table">
            <thead>
              <tr>
                <th class="col-order-number">{{ t('orders.table.orderNumber') }}</th>
                <th class="col-customer">{{ t('orders.table.customer') }}</th>
                <th class="col-items">{{ t('orders.table.items') }}</th>
                <th class="col-status">{{ t('orders.table.status') }}</th>
                <th class="col-date">{{ t('orders.table.orderDate') }}</th>
                <th class="col-date">{{ t('orders.table.expectedDelivery') }}</th>
                <!-- Currency lives in the header instead of being repeated in
                     every cell; the symbol still follows the selected locale. -->
                <th class="col-value num">{{ t('orders.table.totalValue') }} ({{ currencySymbol }})</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
                <td class="col-customer">{{ translateCustomerName(order.customer) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="(item, idx) in order.items" :key="idx" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol }}{{ item.unit_price }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status">
                  <span :class="['badge', getOrderStatusClass(order.status)]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td class="col-date">{{ formatDate(order.order_date) }}</td>
                <td class="col-date">{{ formatDate(order.expected_delivery) }}</td>
                <td class="col-value num"><strong>{{ order.total_value.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="!orders.length" class="state state--empty">
          <p class="state-title">{{ t('common.noData') }}</p>
          <p>{{ t('orders.emptyHint') }} {{ t('common.noDataHint') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Orders',
  setup() {
    const { t, currentCurrency, translateProductName, translateCustomerName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })
    const loading = ref(true)
    const error = ref(null)
    const orders = ref([])

    // Restock orders are independent of the shared filters: they are loaded once
    // and are not affected by the filter watcher below.
    const restockOrders = ref([])
    const restockError = ref(null)
    const restockLoading = ref(false)

    // Restock orders stay USD regardless of locale, matching the Restocking tab.
    const formatUsd = (value) => formatCurrency(value || 0, 'USD')

    // Line-level money keeps its cents so the expanded lines reconcile with the
    // order total; formatCurrency() rounds to whole dollars.
    const formatUsdExact = (value) => formatCurrencyWithDecimals(value || 0, 'USD', 2)

    const loadRestockOrders = async () => {
      try {
        restockLoading.value = true
        restockError.value = null
        restockOrders.value = await api.getRestockOrders()
      } catch (err) {
        restockError.value = 'Failed to load submitted restock orders'
        console.error('Restock orders error:', err)
      } finally {
        restockLoading.value = false
      }
    }

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loadOrders = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        const fetchedOrders = await api.getOrders(filters)

        // Sort orders by order_date (earliest first)
        orders.value = fetchedOrders.sort((a, b) => {
          const dateA = new Date(a.order_date)
          const dateB = new Date(b.order_date)
          return dateA - dateB
        })
      } catch (err) {
        error.value = 'Failed to load orders: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadOrders()
    })

    const getOrdersByStatus = (status) => {
      return orders.value.filter(order => order.status === status)
    }

    const getOrderStatusClass = (status) => {
      const statusMap = {
        'Delivered': 'success',
        'Shipped': 'info',
        'Processing': 'warning',
        'Backordered': 'danger'
      }
      return statusMap[status] || 'info'
    }

    // Restocking dates are date-only (YYYY-MM-DD). new Date() reads those as UTC midnight,
    // which renders as the previous day in any timezone behind UTC, so build a local date.
    const formatRestockDate = (dateString) => {
      const [year, month, day] = String(dateString).split('-').map(Number)
      if (!year || !month || !day) return dateString
      return new Date(year, month - 1, day).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    onMounted(() => {
      loadOrders()
      loadRestockOrders()
    })

    return {
      t,
      loading,
      error,
      orders,
      restockOrders,
      restockError,
      restockLoading,
      formatUsd,
      formatUsdExact,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      formatRestockDate,
      currencySymbol,
      translateProductName,
      translateCustomerName
    }
  }
}
</script>

<style scoped>
/* Fixed table layout to prevent column shifting */
.orders-table {
  table-layout: fixed;
  width: 100%;
}

/* Column widths */
.col-order-number {
  width: 130px;
}

.col-customer {
  width: 180px;
}

.col-items {
  width: 200px;
}

.col-status {
  width: 130px;
}

.col-date {
  width: 140px;
}

.col-value {
  width: 120px;
}

.col-lead {
  width: 140px;
}

/* Restock line items carry more text per row than customer order items */
.restock-dropdown {
  min-width: 420px;
  max-width: 560px;
}

/* Items details styling */
.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: var(--color-accent);
  font-weight: var(--weight-medium);
  list-style: none;
  user-select: none;
  display: inline-block;
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: '▶';
  display: inline-block;
  margin-right: var(--space-1);
  font-size: var(--text-xs);
  transition: transform var(--duration-base) var(--ease);
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-summary:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

/* <summary> isn't covered by the global :focus-visible rule, and this is the
   only way to open the row from the keyboard. */
.items-summary:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: var(--focus-ring-offset);
  border-radius: var(--radius-sm);
}

/* Dropdown container — floats over the table, so it carries a shadow. */
.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: var(--space-2);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: var(--space-3);
  /* Same layer as the sticky table header; later in the DOM, so it wins. */
  z-index: var(--z-sticky);
  min-width: 300px;
  max-width: 400px;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2);
  border-bottom: 1px solid var(--color-border);
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.item-meta {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
</style>
