<template>
  <div class="spending">
    <header class="page-header">
      <div>
        <h2>{{ t('finance.title') }}</h2>
        <p>{{ t('finance.description') }}</p>
      </div>
    </header>

    <!-- Skeletons are sized to the tiles and charts they stand in for, so the
         page doesn't jump the moment the data arrives. -->
    <div v-if="loading" class="stack" role="status" :aria-label="t('common.loading')">
      <div class="skeleton-stats">
        <div v-for="n in 4" :key="n" class="skeleton skeleton-tile"></div>
      </div>
      <div class="skeleton skeleton-chart"></div>
      <div class="skeleton skeleton-chart"></div>
    </div>
    <div v-else-if="error" class="state state--error">
      <p class="state-title">{{ t('common.error') }}</p>
      <p>{{ error }}</p>
    </div>
    <div v-else>
      <!-- Revenue & Financial KPIs -->
      <div class="stats-grid">
        <div class="stat-card revenue-card">
          <div class="stat-label">{{ t('finance.totalRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(revenueMetrics.totalRevenue) }}</div>
          <div class="stat-delta up">
            <span class="change-icon">↑</span>
            {{ t('finance.fromOrders', { count: revenueMetrics.orderCount }) }}
          </div>
        </div>
        <div class="stat-card cost-card">
          <div class="stat-label">{{ t('finance.totalCosts') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCosts) }}</div>
          <div class="stat-meta">{{ t('finance.costBreakdown') }}</div>
        </div>
        <div class="stat-card profit-card">
          <div class="stat-label">{{ t('finance.netProfit') }}</div>
          <div class="stat-value">{{ formatCurrency(netProfit) }}</div>
          <div class="stat-meta">{{ profitMargin }}% {{ t('finance.margin') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('finance.avgOrderValue') }}</div>
          <div class="stat-value">{{ formatCurrency(revenueMetrics.avgOrderValue) }}</div>
          <div class="stat-meta">{{ t('finance.perOrderRevenue') }}</div>
        </div>
      </div>

      <!-- Monthly Revenue vs Cost Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('finance.revenueVsCosts.title') }}</h3>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot revenue-color"></span>{{ t('finance.revenueVsCosts.revenue') }}</span>
            <span class="legend-item"><span class="legend-dot cost-color"></span>{{ t('finance.revenueVsCosts.costs') }}</span>
          </div>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div class="y-axis">
              <span>{{ currencySymbol }}{{ maxRevenueValue }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.75) }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.5) }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.25) }}K</span>
              <span>{{ currencySymbol }}0</span>
            </div>
            <div class="chart-area">
              <div v-for="month in monthlyRevenue" :key="month.month" class="bar-group-revenue">
                <div class="revenue-bars">
                  <div class="revenue-bar" :style="{ height: getRevenueBarHeight(month.revenue) + '%' }" :title="`Revenue: ${currencySymbol}${month.revenue.toLocaleString()}`"></div>
                  <div class="cost-bar" :style="{ height: getRevenueBarHeight(month.costs) + '%' }" :title="`Costs: ${currencySymbol}${month.costs.toLocaleString()}`"></div>
                </div>
                <span class="bar-label">{{ translateMonth(month.month) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Monthly Cost Flow Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('finance.monthlyCostFlow.title') }}</h3>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot procurement"></span>{{ t('finance.monthlyCostFlow.procurement') }}</span>
            <span class="legend-item"><span class="legend-dot operational"></span>{{ t('finance.monthlyCostFlow.operational') }}</span>
            <span class="legend-item"><span class="legend-dot labor"></span>{{ t('finance.monthlyCostFlow.labor') }}</span>
            <span class="legend-item"><span class="legend-dot overhead"></span>{{ t('finance.monthlyCostFlow.overhead') }}</span>
          </div>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div class="y-axis">
              <span>{{ currencySymbol }}25K</span>
              <span>{{ currencySymbol }}20K</span>
              <span>{{ currencySymbol }}15K</span>
              <span>{{ currencySymbol }}10K</span>
              <span>{{ currencySymbol }}5K</span>
              <span>{{ currencySymbol }}0</span>
            </div>
            <div class="chart-area">
              <div v-for="month in monthlySpending" :key="month.month" class="bar-group">
                <div class="stacked-bar" @click="showCostDetail(month)">
                  <div class="bar-segment procurement" :style="{ height: getBarHeight(month.procurement) + '%' }" :title="`Procurement: ${currencySymbol}${month.procurement.toLocaleString()}`"></div>
                  <div class="bar-segment operational" :style="{ height: getBarHeight(month.operational) + '%' }" :title="`Operational: ${currencySymbol}${month.operational.toLocaleString()}`"></div>
                  <div class="bar-segment labor" :style="{ height: getBarHeight(month.labor) + '%' }" :title="`Labor: ${currencySymbol}${month.labor.toLocaleString()}`"></div>
                  <div class="bar-segment overhead" :style="{ height: getBarHeight(month.overhead) + '%' }" :title="`Overhead: ${currencySymbol}${month.overhead.toLocaleString()}`"></div>
                </div>
                <span class="bar-label">{{ translateMonth(month.month) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="two-column-grid">
        <!-- Category Spending Breakdown -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('finance.categorySpending.title') }}</h3>
          </div>
          <div v-if="categorySpending.length" class="category-list">
            <div v-for="category in categorySpending" :key="category.category" class="category-item">
              <div class="category-info">
                <div class="category-name">{{ translateCategory(category.category) }}</div>
                <div class="category-amount num">{{ currencySymbol }}{{ category.amount.toLocaleString() }}</div>
              </div>
              <div class="category-bar-container">
                <div class="category-bar" :style="{ width: category.percentage + '%' }"></div>
              </div>
              <div class="category-meta">
                <span class="percentage">{{ category.percentage }}% {{ t('finance.categorySpending.ofTotal') }}</span>
                <span class="change" :class="{ positive: category.change > 0, negative: category.change < 0 }">
                  {{ category.change > 0 ? '+' : '' }}{{ category.change }}%
                </span>
              </div>
            </div>
          </div>
          <div v-else class="state state--empty">
            <p class="state-title">{{ t('common.noData') }}</p>
            <p>Spending by category appears once purchase transactions are recorded for the selected period.</p>
          </div>
        </div>

        <!-- Recent Transactions -->
        <div class="card card--flush transactions-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('finance.transactions.title') }}</h3>
          </div>
          <div v-if="recentTransactions.length" class="table-container transactions-scroll">
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ t('finance.transactions.id') }}</th>
                  <th>{{ t('finance.transactions.description') }}</th>
                  <th>{{ t('finance.transactions.vendor') }}</th>
                  <th>{{ t('finance.transactions.date') }}</th>
                  <th class="num">{{ t('finance.transactions.amount') }} ({{ currencySymbol }})</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="transaction in recentTransactions"
                  :key="transaction.id"
                  class="is-clickable"
                  @click="handleTransactionClick(transaction)"
                >
                  <td class="transaction-id">{{ transaction.id.toString().padStart(3, '0') }}</td>
                  <td class="transaction-description">{{ transaction.description }}</td>
                  <td class="transaction-vendor">{{ transaction.vendor }}</td>
                  <td class="transaction-date">{{ formatDateShort(transaction.date) }}</td>
                  <td class="transaction-amount num">{{ transaction.amount.toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="state state--empty">
            <p class="state-title">{{ t('common.noData') }}</p>
            <p>Transactions posted in the selected period appear here. Widen the time filter to see earlier spending.</p>
          </div>
        </div>
      </div>
    </div>

    <CostDetailModal
      :is-open="showCostModal"
      :cost-data="selectedCostData"
      @close="showCostModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil } from '../utils/currency'
import CostDetailModal from '../components/CostDetailModal.vue'

export default {
  name: 'Spending',
  components: {
    CostDetailModal
  },
  setup() {
    const { t, currentCurrency } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allMonthlySpending = ref([])
    const allCategorySpending = ref([])
    const allTransactions = ref([])
    const summaryData = ref({})
    const allOrders = ref([])

    // Modal state
    const showCostModal = ref(false)
    const selectedCostData = ref(null)

    // Use shared filters
    const { selectedPeriod, getCurrentFilters } = useFilters()

    // Monthly spending chart always shows all months (not filtered)
    const monthlySpending = computed(() => {
      return allMonthlySpending.value
    })

    // Filtered monthly spending for summary calculations only
    const filteredMonthlySpending = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allMonthlySpending.value
      }

      // Extract month name from YYYY-MM format
      const monthMap = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
      }
      const selectedMonth = monthMap[selectedPeriod.value.split('-')[1]]
      return allMonthlySpending.value.filter(m => m.month === selectedMonth)
    })

    const categorySpending = computed(() => {
      return allCategorySpending.value
    })

    const recentTransactions = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allTransactions.value
      }
      // Filter transactions by selected month
      return allTransactions.value.filter(t => {
        const transactionMonth = new Date(t.date).toISOString().slice(0, 7)
        return transactionMonth === selectedPeriod.value
      })
    })

    const summary = computed(() => {
      // Recalculate summary based on filteredMonthlySpending (not the chart data)
      if (filteredMonthlySpending.value.length === 0) {
        return summaryData.value
      }

      const totals = filteredMonthlySpending.value.reduce((acc, month) => ({
        procurement: acc.procurement + month.procurement,
        operational: acc.operational + month.operational,
        labor: acc.labor + month.labor,
        overhead: acc.overhead + month.overhead
      }), { procurement: 0, operational: 0, labor: 0, overhead: 0 })

      return {
        total_procurement_cost: totals.procurement,
        total_operational_cost: totals.operational,
        total_labor_cost: totals.labor,
        total_overhead: totals.overhead,
        procurement_change: summaryData.value.procurement_change || 0,
        operational_change: summaryData.value.operational_change || 0,
        labor_change: summaryData.value.labor_change || 0,
        overhead_change: summaryData.value.overhead_change || 0
      }
    })

    // Filtered orders based on selected period
    const filteredOrders = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allOrders.value
      }

      // Filter orders by selected month
      return allOrders.value.filter(order => {
        const orderMonth = new Date(order.order_date).toISOString().slice(0, 7)
        return orderMonth === selectedPeriod.value
      })
    })

    // Revenue metrics from filtered orders
    const revenueMetrics = computed(() => {
      const totalRevenue = filteredOrders.value.reduce((sum, order) => sum + (order.total_value || 0), 0)
      const orderCount = filteredOrders.value.length
      const avgOrderValue = orderCount > 0 ? totalRevenue / orderCount : 0

      return {
        totalRevenue,
        orderCount,
        avgOrderValue,
        revenueGrowth: 15.3 // Placeholder - could calculate from historical data
      }
    })

    // Total costs from summary
    const totalCosts = computed(() => {
      return summary.value.total_procurement_cost +
             summary.value.total_operational_cost +
             summary.value.total_labor_cost +
             summary.value.total_overhead
    })

    // Net profit
    const netProfit = computed(() => {
      return revenueMetrics.value.totalRevenue - totalCosts.value
    })

    // Profit margin percentage
    const profitMargin = computed(() => {
      if (revenueMetrics.value.totalRevenue === 0) return 0
      return ((netProfit.value / revenueMetrics.value.totalRevenue) * 100).toFixed(1)
    })

    // Monthly revenue data for chart
    const monthlyRevenue = computed(() => {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

      // Initialize all months
      const revenueByMonth = monthNames.map(month => ({
        month,
        revenue: 0,
        costs: 0
      }))

      // Calculate revenue from orders
      allOrders.value.forEach(order => {
        const orderDate = new Date(order.order_date)
        const monthIndex = orderDate.getMonth()
        if (monthIndex >= 0 && monthIndex < 12) {
          revenueByMonth[monthIndex].revenue += order.total_value || 0
        }
      })

      // Add costs from spending data
      allMonthlySpending.value.forEach(spending => {
        const monthIndex = monthNames.indexOf(spending.month)
        if (monthIndex >= 0) {
          revenueByMonth[monthIndex].costs = spending.procurement + spending.operational + spending.labor + spending.overhead
        }
      })

      return revenueByMonth
    })

    // Max value for chart scaling
    const maxRevenueValue = computed(() => {
      const maxRevenue = Math.max(...monthlyRevenue.value.map(m => m.revenue))
      const maxCost = Math.max(...monthlyRevenue.value.map(m => m.costs))
      const max = Math.max(maxRevenue, maxCost)
      return Math.ceil(max / 1000) // Return in K
    })

    const loadData = async () => {
      try {
        loading.value = true
        const [summaryRes, monthlyRes, categoryRes, transactionsRes, ordersRes] = await Promise.all([
          api.getSpendingSummary(),
          api.getMonthlySpending(),
          api.getCategorySpending(),
          api.getTransactions(),
          api.getOrders()
        ])

        summaryData.value = summaryRes
        allMonthlySpending.value = monthlyRes
        allCategorySpending.value = categoryRes
        allTransactions.value = transactionsRes
        allOrders.value = ordersRes
      } catch (err) {
        error.value = 'Failed to load financial data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for period filter changes
    watch([selectedPeriod], () => {
      // Data will automatically update via computed properties
    })

    const formatCurrency = (value) => {
      return formatCurrencyUtil(value, currentCurrency.value)
    }

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const getBarHeight = (value) => {
      const maxValue = 25000
      return (value / maxValue) * 100
    }

    const getRevenueBarHeight = (value) => {
      const maxValue = maxRevenueValue.value * 1000
      return (value / maxValue) * 100
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    }

    const formatDateShort = (dateString) => {
      const date = new Date(dateString)
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      const year = date.getFullYear().toString().slice(-2)
      return `${month}/${day}/${year}`
    }

    const translateMonth = (month) => {
      const monthMap = {
        'Jan': t('months.jan'),
        'Feb': t('months.feb'),
        'Mar': t('months.mar'),
        'Apr': t('months.apr'),
        'May': t('months.may'),
        'Jun': t('months.jun'),
        'Jul': t('months.jul'),
        'Aug': t('months.aug'),
        'Sep': t('months.sep'),
        'Oct': t('months.oct'),
        'Nov': t('months.nov'),
        'Dec': t('months.dec')
      }
      return monthMap[month] || month
    }

    const translateCategory = (category) => {
      // First try spending categories
      const spendingCategoryMap = {
        'Raw Materials': t('spendingCategories.rawMaterials'),
        'Components': t('spendingCategories.components'),
        'Equipment': t('spendingCategories.equipment'),
        'Consumables': t('spendingCategories.consumables')
      }

      // Then try product categories
      const productCategoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }

      return spendingCategoryMap[category] || productCategoryMap[category] || category
    }

    const handleTransactionClick = (transaction) => {
      console.log('Transaction clicked:', transaction)
      alert(`Transaction Details:\n\nID: ${transaction.id}\nDescription: ${transaction.description}\nVendor: ${transaction.vendor}\nDate: ${formatDateShort(transaction.date)}\nAmount: $${transaction.amount.toLocaleString()}`)
    }

    const showCostDetail = (monthData) => {
      selectedCostData.value = monthData
      showCostModal.value = true
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      summary,
      monthlySpending,
      categorySpending,
      recentTransactions,
      revenueMetrics,
      totalCosts,
      netProfit,
      profitMargin,
      monthlyRevenue,
      maxRevenueValue,
      formatCurrency,
      currencySymbol,
      getBarHeight,
      getRevenueBarHeight,
      formatDate,
      formatDateShort,
      translateMonth,
      translateCategory,
      handleTransactionClick,
      showCostModal,
      selectedCostData,
      showCostDetail,
      Math
    }
  }
}
</script>

<style scoped>
/* --- Chart series palette ---------------------------------------------------
   The cost-flow and revenue series are categorical — they answer "which line of
   spending is this", not "is this good or bad" — so they draw on the token
   file's --series-* slots rather than the status colours. Status hues are
   reserved: a bar drawn in --danger-solid reads as a failing bar, not as
   "overhead". Slots are assigned in order within each chart and never cycled,
   so a series keeps its colour when a filter removes the one above it.

   Named aliases rather than raw slot numbers, because one definition is what
   keeps a legend swatch and the bar it labels from drifting apart. */
.spending {
  /* Cost flow: four stacked categories. */
  --series-procurement: var(--series-1);
  --series-operational: var(--series-2);
  --series-labor: var(--series-3);
  --series-overhead: var(--series-4);

  /* Revenue vs cost: a separate chart, so its slots start again at 1. */
  --series-revenue: var(--series-1);
  --series-cost: var(--series-2);

  /* Chart geometry: the plot height, and the strip below the plot floor that
     the month labels sit in. Both charts share them so their baselines line up. */
  --chart-height: 350px;
  --chart-label-gutter: var(--space-8);
}

/* The shared .state stacks with flex `gap`; UA paragraph margins would double it. */
.state p {
  margin: 0;
}

/* --- Loading skeletons ---------------------------------------------------- */

.skeleton-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
}

.skeleton-tile {
  height: 112px;
}

.skeleton-chart {
  height: var(--chart-height);
}

/* --- KPI tiles ------------------------------------------------------------ */

/* The three headline tiles carry the colour of their series in the charts
   below, so the eye can connect "Total Costs" to the red bars without a
   legend. Written as `.stat-card.x` so the shared hover rule, which sets
   `border-color` on all four sides, cannot grey the accent edge out. */
.stat-card.revenue-card { border-left: 4px solid var(--series-revenue); }
.stat-card.cost-card { border-left: 4px solid var(--series-cost); }
.stat-card.profit-card { border-left: 4px solid var(--accent-500); }

.stat-meta {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* --- Charts --------------------------------------------------------------- */

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  font-size: var(--text-sm);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
}

.legend-dot {
  width: 12px;
  height: 12px;
  /* Half of --radius-sm: a 12px swatch needs a proportionally smaller corner,
     and a fully rounded dot reads as a different shape language to the bars. */
  border-radius: 3px;
}

.legend-dot.procurement { background: var(--series-procurement); }
.legend-dot.operational { background: var(--series-operational); }
.legend-dot.labor { background: var(--series-labor); }
.legend-dot.overhead { background: var(--series-overhead); }
.legend-dot.revenue-color { background: var(--series-revenue); }
.legend-dot.cost-color { background: var(--series-cost); }

.chart-container {
  padding: var(--space-6) 0;
}

.bar-chart {
  display: flex;
  gap: var(--space-6);
  height: var(--chart-height);
}

.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: var(--space-4);
  /* The axis stops at the plot floor rather than the bottom of the month
     labels, so the "0" tick sits level with the foot of the bars. */
  padding-bottom: var(--chart-label-gutter);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
  border-right: 1px solid var(--color-border);
}

.chart-area {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: var(--space-2);
}

.bar-group,
.bar-group-revenue {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
}

.revenue-bars {
  width: 100%;
  max-width: 80px;
  display: flex;
  gap: var(--space-1);
  justify-content: center;
  align-items: flex-end;
  height: 100%;
  padding-bottom: var(--chart-label-gutter);
}

.revenue-bar,
.cost-bar {
  width: 50%;
  max-width: 30px;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  /* `height` stays in the transition list: the bars are sized from the data,
     so dropping it would remove the grow-in when the period filter changes. */
  transition: height var(--duration-slow) var(--ease),
    opacity var(--duration-fast) var(--ease),
    transform var(--duration-fast) var(--ease);
  cursor: pointer;
  min-height: 4px; /* a near-zero month still reads as a bar, not a gap */
}

.revenue-bar { background: var(--series-revenue); }
.cost-bar { background: var(--series-cost); }

.revenue-bar:hover,
.cost-bar:hover {
  opacity: 0.8;
  transform: scaleY(1.05);
}

.stacked-bar {
  width: 100%;
  max-width: 60px;
  display: flex;
  flex-direction: column-reverse;
  align-items: stretch;
  height: 100%;
  padding-bottom: var(--chart-label-gutter);
  cursor: pointer;
  transition: opacity var(--duration-fast) var(--ease);
}

.stacked-bar:hover {
  opacity: 0.85;
}

.bar-segment {
  width: 100%;
  display: block;
  cursor: pointer;
  transition: height var(--duration-slow) var(--ease),
    opacity var(--duration-fast) var(--ease);
}

.bar-segment:first-child { border-radius: 0 0 var(--radius-sm) var(--radius-sm); }
.bar-segment:last-child { border-radius: var(--radius-sm) var(--radius-sm) 0 0; }

.bar-segment.procurement { background: var(--series-procurement); }
.bar-segment.operational { background: var(--series-operational); }
.bar-segment.labor { background: var(--series-labor); }
.bar-segment.overhead { background: var(--series-overhead); }

.bar-segment:hover {
  opacity: 0.8;
}

.bar-label {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text-muted);
}

/* --- Two-column section --------------------------------------------------- */

.two-column-grid {
  display: grid;
  /* min() keeps the 450px track from forcing a horizontal scrollbar on a phone,
     where the track would otherwise be wider than the viewport. */
  grid-template-columns: repeat(auto-fit, minmax(min(450px, 100%), 1fr));
  gap: var(--space-6);
}

/* Inside the grid the gap does the spacing; the card's own margin would add a
   second, uneven gutter under the shorter column. */
.two-column-grid > .card {
  margin-bottom: 0;
}

/* --- Category spending ---------------------------------------------------- */

.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-3);
}

.category-name {
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

/* Weight, not colour, carries the emphasis: the accent is spent on the bar
   below, which is what the figure is being compared against. */
.category-amount {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  color: var(--color-text);
}

.category-bar-container {
  width: 100%;
  height: var(--space-2);
  background: var(--color-surface-sunken);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.category-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-500) 0%, var(--accent-600) 100%);
  border-radius: var(--radius-pill);
  transition: width var(--duration-slow) var(--ease);
}

.category-meta {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
}

.percentage {
  color: var(--color-text-muted);
}

.change {
  font-weight: var(--weight-semibold);
}

.change.positive { color: var(--success-solid); }
.change.negative { color: var(--danger-solid); }

/* --- Transactions --------------------------------------------------------- */

.transactions-card {
  display: flex;
  flex-direction: column;
}

/* The table scrolls inside the card so the two columns keep a comparable
   height. This element is the scroll container, so the sticky header from
   .data-table sticks to its top edge rather than the page's. */
.transactions-scroll {
  overflow-y: auto;
  max-height: 400px;
}

/* Rows open a transaction detail; the accent tint on hover is the affordance
   the old private table styling carried, kept on top of the shared hover. */
.data-table tbody tr.is-clickable:hover {
  background: var(--color-accent-surface);
}

.transaction-id {
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
}

.transaction-description {
  color: var(--color-text);
  font-weight: var(--weight-medium);
}

.transaction-vendor {
  color: var(--color-text-muted);
}

.transaction-date {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
}

.transaction-amount {
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

/* Matches the breakpoint in tokens.css; CSS variables can't be used in a media
   query, so the literal is duplicated on purpose. */
@media (max-width: 768px) {
  .spending {
    --chart-height: 240px;
    --chart-label-gutter: var(--space-6);
  }

  /* Twelve months plus a four-item legend is more than a phone row holds. */
  .spending .card-header {
    flex-wrap: wrap;
  }

  .chart-legend {
    gap: var(--space-3);
    font-size: var(--text-xs);
  }

  /* Twelve month columns will not compress to phone width without the labels
     colliding, so the plot scrolls sideways while the y-axis labels stay put
     (they are a sibling of .chart-area, not a child). overflow-y is pinned
     explicitly because a lone overflow-x:auto computes the other axis to auto
     and lays a spurious vertical scrollbar across the bars. */
  .chart-area {
    overflow-x: auto;
    overflow-y: hidden;
    justify-content: flex-start;
  }

  /* A fixed basis rather than flex:1 — flex items floor at their min-content
     width (the month label), so shrinking them just pushed the overflow onto
     the page instead of into this scroller. */
  .bar-group,
  .bar-group-revenue {
    flex: 0 0 34px;
  }
}
</style>
