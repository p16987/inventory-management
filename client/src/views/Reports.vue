<template>
  <div class="reports">
    <div class="page-header">
      <div>
        <h2>{{ t('reports.title') }}</h2>
        <p>{{ t('reports.description') }}</p>
      </div>
    </div>

    <!-- Skeleton rows stand in for the report tables so the page holds its
         height while loading instead of jumping when the data arrives. The
         loading string stays for screen readers. -->
    <div v-if="loading" class="stack" aria-busy="true">
      <span class="sr-only">{{ t('common.loading') }}</span>
      <div v-for="n in 6" :key="n" class="skeleton skeleton-row"></div>
    </div>
    <div v-else-if="error" class="state state--error">
      <p class="state-title">{{ t('reports.loadError') }}</p>
      <p>{{ error }}</p>
    </div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card card--flush">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th class="num">{{ t('reports.quarterly.totalOrders') }}</th>
                <!-- Currency lives in the header rather than in every cell; the
                     symbol follows the selected locale. -->
                <th class="num">{{ t('reports.quarterly.totalRevenue') }} ({{ currencySymbol }})</th>
                <th class="num">{{ t('reports.quarterly.avgOrderValue') }} ({{ currencySymbol }})</th>
                <th class="col-fit">{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td class="num">{{ q.total_orders }}</td>
                <td class="num">{{ formatAmount(q.total_revenue) }}</td>
                <td class="num">{{ formatAmount(q.avg_order_value) }}</td>
                <td class="col-fit">
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="!quarterlyData.length" class="state state--empty">
          <p class="state-title">{{ t('reports.quarterly.empty') }}</p>
          <p>{{ t('reports.quarterly.emptyHint') }} {{ t('common.noDataHint') }}</p>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthly.title') }}</h3>
        </div>
        <div v-if="monthlyData.length" class="chart-container">
          <div class="bar-chart">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatMoney(month.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
        <div v-else class="state state--empty">
          <p class="state-title">{{ t('reports.monthly.empty') }}</p>
          <p>{{ t('reports.monthly.emptyHint') }} {{ t('common.noDataHint') }}</p>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card card--flush">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.comparison.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ t('reports.comparison.month') }}</th>
                <th class="num">{{ t('reports.comparison.orders') }}</th>
                <th class="num">{{ t('reports.comparison.revenue') }} ({{ currencySymbol }})</th>
                <th class="num">{{ t('reports.comparison.change') }}</th>
                <th class="num">{{ t('reports.comparison.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td class="num">{{ month.order_count }}</td>
                <td class="num">{{ formatAmount(month.revenue) }}</td>
                <td class="num">
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td class="num">
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="!monthlyData.length" class="state state--empty">
          <p class="state-title">{{ t('reports.comparison.empty') }}</p>
          <p>{{ t('reports.comparison.emptyHint') }} {{ t('common.noDataHint') }}</p>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalOrders') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { convertAmount, formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Height of .bar-container in the scoped styles; every bar is scaled against it.
const CHART_MAX_HEIGHT = 200

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

    const intlLocale = computed(() => (currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'))

    const loadData = async () => {
      try {
        loading.value = true
        // Cleared on every attempt, otherwise one failed load would leave the
        // error state on screen even after a later filter change succeeds.
        error.value = null

        const filters = getCurrentFilters()
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])

        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        error.value = err.message
        console.error('Reports error:', err)
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    // Summary stats are derived rather than assigned, so they can't fall out of
    // step with the rows after a filter-triggered reload.
    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, month) => sum + (Number(month.revenue) || 0), 0)
    )

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length ? totalRevenue.value / monthlyData.value.length : 0
    )

    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, month) => sum + (Number(month.order_count) || 0), 0)
    )

    const bestQuarter = computed(() => {
      const best = quarterlyData.value.reduce((winner, q) => {
        if (!winner || (Number(q.total_revenue) || 0) > (Number(winner.total_revenue) || 0)) return q
        return winner
      }, null)
      return best ? best.quarter : t('reports.notAvailable')
    })

    // Computed once per data change instead of once per bar, which is what the
    // previous per-bar scan of monthlyData did on every render.
    const maxRevenue = computed(() =>
      monthlyData.value.reduce((max, month) => Math.max(max, Number(month.revenue) || 0), 0)
    )

    // Bare grouped number for table cells: the column header carries the
    // symbol, but the value still converts and groups per the active locale.
    const formatAmount = (value) => {
      const amount = convertAmount(Number(value) || 0, currentCurrency.value)
      const fractionDigits = currentCurrency.value === 'JPY' ? 0 : 2
      return amount.toLocaleString(intlLocale.value, {
        minimumFractionDigits: fractionDigits,
        maximumFractionDigits: fractionDigits
      })
    }

    // Symbol included, for stat tiles and the chart tooltip.
    const formatMoney = (value) => formatCurrency(Number(value) || 0, currentCurrency.value)

    const formatMonth = (monthStr) => {
      const [year, month] = String(monthStr).split('-')
      const monthIndex = parseInt(month, 10) - 1
      // A malformed key would otherwise index past the month array and render
      // as "undefined 2025"; show the raw value instead.
      if (!Number.isInteger(monthIndex) || monthIndex < 0 || monthIndex > 11) {
        return String(monthStr)
      }
      return new Date(Number(year), monthIndex).toLocaleDateString(intlLocale.value, {
        year: 'numeric',
        month: 'short'
      })
    }

    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0
      return ((Number(revenue) || 0) / maxRevenue.value) * CHART_MAX_HEIGHT
    }

    const getFulfillmentClass = (rate) => {
      const value = Number(rate) || 0
      if (value >= 90) return 'badge success'
      if (value >= 75) return 'badge warning'
      return 'badge danger'
    }

    const getChangeValue = (current, previous) => {
      const change = (Number(current) || 0) - (Number(previous) || 0)
      const sign = change > 0 ? '+' : change < 0 ? '-' : ''
      // Deltas keep their cents in USD so the column reconciles with revenue.
      return sign + formatCurrencyWithDecimals(Math.abs(change), currentCurrency.value, 2)
    }

    const getChangeClass = (current, previous) => {
      const change = (Number(current) || 0) - (Number(previous) || 0)
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    const getGrowthRate = (current, previous) => {
      const base = Number(previous) || 0
      if (base === 0) return t('reports.notAvailable')

      const rate = (((Number(current) || 0) - base) / base) * 100
      const sign = rate > 0 ? '+' : ''
      return sign + rate.toFixed(1) + '%'
    }

    onMounted(() => {
      loadData()
    })

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyData,
      currencySymbol,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      formatAmount,
      formatMoney,
      formatMonth,
      getBarHeight,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate
    }
  }
}
</script>

<style scoped>
/* Only the revenue bar chart is specific to this view; cards, tables, badges,
   stat tiles and the state blocks now come from styles/primitives.css. */

.chart-container {
  padding: var(--space-8) var(--space-4);
  /* Geometry, not spacing: the track plus the rotated labels need this room. */
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: var(--space-2);
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  /* Must stay 200px: getBarHeight() scales every bar against that maximum. */
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, var(--accent-600), var(--accent-500));
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: background var(--duration-base) var(--ease);
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, var(--accent-700), var(--accent-600));
}

.bar-label {
  margin-top: var(--space-6);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

/* Direction of change is set from the script via getChangeClass(). */
.positive-change {
  color: var(--success-solid);
  font-weight: var(--weight-semibold);
}

.negative-change {
  color: var(--danger-solid);
  font-weight: var(--weight-semibold);
}
</style>
