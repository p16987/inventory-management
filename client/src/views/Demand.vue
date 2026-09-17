<template>
  <div class="demand">
    <div class="page-header">
      <div>
        <h2>{{ t('demand.title') }}</h2>
        <p>{{ t('demand.description') }}</p>
      </div>
    </div>

    <div v-if="loading" class="stack" :aria-label="t('common.loading')" aria-busy="true">
      <div v-for="n in 6" :key="n" class="skeleton skeleton-row" />
    </div>
    <div v-else-if="error" class="state state--error">
      <p class="state-title">{{ t('common.error') }}</p>
      <p>{{ error }}</p>
    </div>
    <div v-else>
      <div class="stats-grid demand-trend-cards">
        <div class="stat-card trend-card increasing-card">
          <div class="trend-header">
            <div class="trend-icon badge increasing" aria-hidden="true">↑</div>
            <div>
              <div class="stat-label">{{ t('demand.increasingDemand') }}</div>
              <div class="stat-value trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('increasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('increasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name truncate">{{ item.item_name }}</span>
              <span class="item-change">+{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('increasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('increasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="stat-card trend-card stable-card">
          <div class="trend-header">
            <div class="trend-icon badge stable" aria-hidden="true">→</div>
            <div>
              <div class="stat-label">{{ t('demand.stableDemand') }}</div>
              <div class="stat-value trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('stable').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('stable').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name truncate">{{ item.item_name }}</span>
              <span class="item-change neutral">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('stable').length > 5" class="more-items">
              +{{ getForecastsByTrend('stable').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="stat-card trend-card decreasing-card">
          <div class="trend-header">
            <div class="trend-icon badge decreasing" aria-hidden="true">↓</div>
            <div>
              <div class="stat-label">{{ t('demand.decreasingDemand') }}</div>
              <div class="stat-value trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('decreasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('decreasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name truncate">{{ item.item_name }}</span>
              <span class="item-change">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('decreasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('decreasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>
      </div>

      <div class="card card--flush">
        <div class="card-header">
          <h3 class="card-title">{{ t('demand.demandForecasts') }}</h3>
          <span class="card-subtitle">{{ t('demand.itemsCount', { count: forecasts.length }) }}</span>
        </div>
        <div v-if="!forecasts.length" class="state state--empty">
          <p class="state-title">{{ t('common.noData') }}</p>
          <p>{{ t('demand.emptyHint') }} {{ t('common.noDataHint') }}</p>
        </div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ t('demand.table.sku') }}</th>
                <th>{{ t('demand.table.itemName') }}</th>
                <th class="num">{{ t('demand.table.currentDemand') }}</th>
                <th class="num">{{ t('demand.table.forecastedDemand') }}</th>
                <th class="num">{{ t('demand.table.change') }} (%)</th>
                <th class="col-fit">{{ t('demand.table.trend') }}</th>
                <th>{{ t('demand.table.period') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="forecast in forecasts" :key="forecast.id">
                <td><strong>{{ forecast.item_sku }}</strong></td>
                <td>{{ forecast.item_name }}</td>
                <td class="num">{{ forecast.current_demand }}</td>
                <td class="num"><strong>{{ forecast.forecasted_demand }}</strong></td>
                <td class="num">
                  <!-- Colour still comes from getChangeColor(): it encodes the ±2%
                       "effectively stable" rule, which no CSS class here reproduces. -->
                  <span :style="{ color: getChangeColor(forecast) }">
                    {{ getChangePercent(forecast) }}
                  </span>
                </td>
                <td class="col-fit">
                  <span :class="['badge', forecast.trend]">
                    {{ t(`trends.${forecast.trend}`) }}
                  </span>
                </td>
                <td>{{ translatePeriod(forecast.period) }}</td>
              </tr>
            </tbody>
          </table>
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

export default {
  name: 'Demand',
  setup() {
    const { t } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Filter forecasts based on inventory filters
    const forecasts = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allForecasts.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allForecasts.value.filter(f => validSkus.has(f.item_sku))
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadForecasts()
    })

    const getForecastsByTrend = (trend) => {
      return forecasts.value.filter(f => f.trend === trend)
    }

    const getChangePercent = (forecast) => {
      const change = ((forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand * 100).toFixed(1)
      return change > 0 ? `+${change}` : change
    }

    const getChangeColor = (forecast) => {
      const change = forecast.forecasted_demand - forecast.current_demand
      const changePercent = Math.abs((change / forecast.current_demand) * 100)

      // If change is within ±2%, consider it stable and show blue
      if (changePercent <= 2) {
        return '#3b82f6' // Blue for stable
      }

      if (change > 0) return '#10b981' // Green for increasing
      if (change < 0) return '#ef4444' // Red for decreasing
      return '#3b82f6' // Blue for no change
    }

    const translatePeriod = (period) => {
      // Period values like "Next 3 months", "Q1 2025", "30 days", etc.
      const { currentLocale } = useI18n()
      if (currentLocale.value === 'ja') {
        return period
          .replace(/Next\s+/i, '次の')
          .replace(/\s+months/i, 'か月')
          .replace(/\s+month/i, 'か月')
          .replace(/\s+days/i, '日間')
          .replace(/\s+day/i, '日')
          .replace('Q1', '第1四半期')
          .replace('Q2', '第2四半期')
          .replace('Q3', '第3四半期')
          .replace('Q4', '第4四半期')
      }
      return period
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      forecasts,
      getForecastsByTrend,
      getChangePercent,
      getChangeColor,
      translatePeriod
    }
  }
}
</script>

<style scoped>
/* Surface, border, radius, padding and hover all come from .stat-card. The only
   thing genuinely specific here is the width: these tiles carry a list of items,
   so they need more room than the 240px stat-tile track allows. */
.demand-trend-cards {
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

/* Tone strip on the card edge. It reuses the same status tokens the .badge
   variants map to, so the strip and the badge inside it can never disagree. */
.trend-card {
  border-left-width: 4px;
}

.increasing-card { border-left-color: var(--success-solid); }
.stable-card { border-left-color: var(--info-solid); }
.decreasing-card { border-left-color: var(--danger-solid); }

.trend-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

/* The glyph is a .badge for its colours (increasing/stable/decreasing); this
   only resizes it into a 48px square tile. The trend word sits beside it, so
   the arrow never has to carry the meaning on colour alone. */
.trend-icon {
  width: 48px;
  height: 48px;
  justify-content: center;
  padding: 0;
  border-radius: var(--radius-md);
  font-size: var(--text-2xl);
  font-weight: var(--weight-bold);
  flex-shrink: 0;
}

/* The count reads "12 items", not a bare figure, so it takes the section-heading
   size rather than the hero-metric size .stat-value uses for pure numbers. */
.trend-count {
  font-size: var(--text-xl);
  margin-top: var(--space-1);
}

.trend-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  transition: background-color var(--duration-fast) var(--ease);
}

.trend-item:hover {
  background: var(--color-surface-hover);
}

.item-name {
  font-size: var(--text-sm);
  color: var(--color-text);
  font-weight: var(--weight-medium);
  flex: 1;
  /* Without this a flex child refuses to shrink, and .truncate never fires. */
  min-width: 0;
}

.item-change {
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.increasing-card .item-change { color: var(--success-solid); }
.stable-card .item-change { color: var(--info-solid); }
.decreasing-card .item-change { color: var(--danger-solid); }
.item-change.neutral { color: var(--color-text-muted); }

.more-items {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-2);
}
</style>
