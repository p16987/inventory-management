<template>
  <div class="restocking">
    <div class="page-header">
      <div>
        <h2>Restocking</h2>
        <p>Set a purchasing budget and review the recommended restock plan before submitting an order.</p>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Purchasing Budget</h3>
        <div class="stat-value">{{ formatUsd(budget) }}</div>
      </div>
      <div class="budget-control">
        <span class="budget-bound">{{ formatUsd(BUDGET_MIN) }}</span>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          :min="BUDGET_MIN"
          :max="BUDGET_MAX"
          :step="BUDGET_STEP"
          aria-label="Purchasing budget"
        />
        <span class="budget-bound">{{ formatUsd(BUDGET_MAX) }}</span>
      </div>
      <p class="budget-hint">
        Covering every outstanding shortfall currently costs about {{ formatUsd(FULL_COVERAGE_ESTIMATE) }}.
      </p>
    </div>

    <!-- Result of the last submit attempt, shown inline instead of an alert() -->
    <div v-if="submitError" class="state state--error">
      <p class="state-title">Restock order not placed</p>
      <p>{{ submitError }}</p>
    </div>
    <div v-if="placedOrder" class="confirmation">
      <div class="confirmation-title">Restock order {{ placedOrder.order_number }} submitted</div>
      <div class="confirmation-details">
        <span>Total cost: <strong>{{ formatUsdExact(placedOrder.total_cost) }}</strong></span>
        <span>Expected delivery: <strong>{{ formatDate(placedOrder.expected_delivery) }}</strong></span>
        <span>Items: <strong>{{ placedOrder.items.length }}</strong></span>
      </div>
    </div>

    <!-- Skeletons are sized to the real plan rows so the page doesn't jump when
         a debounced budget change lands. -->
    <div v-if="loading" class="card" aria-busy="true">
      <span class="sr-only">Loading recommendations...</span>
      <div v-for="n in 6" :key="n" class="skeleton skeleton-row" />
    </div>
    <div v-else-if="error" class="state state--error">
      <p class="state-title">Couldn't load restock recommendations</p>
      <p>{{ error }}</p>
    </div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">Budget</div>
          <div class="stat-value">{{ formatUsd(appliedBudget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Plan Total Cost</div>
          <div class="stat-value">{{ formatUsdExact(totalCost) }}</div>
        </div>
        <div :class="['stat-card', skippedCount > 0 ? 'warning' : 'success']">
          <div class="stat-label">Remaining Budget</div>
          <div class="stat-value">{{ formatUsd(remainingBudget) }}</div>
        </div>
        <div :class="['stat-card', skippedCount > 0 ? 'warning' : 'info']">
          <div class="stat-label">Items In Plan</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Restock Plan ({{ recommendations.length }})</h3>
          <button
            class="btn btn--primary"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="state state--empty">
          <p class="state-title">No items fit this budget</p>
          <p>Items with a forecast shortfall appear here once the budget covers at least one of them. Drag the budget slider up to see recommendations.</p>
        </div>

        <template v-else>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Item Name</th>
                  <th>Category</th>
                  <th class="num">On Hand</th>
                  <th class="num">Forecast</th>
                  <th class="num">Shortfall</th>
                  <th class="num">Recommended Qty</th>
                  <th class="num">Unit Cost</th>
                  <th class="num">Line Total</th>
                  <th class="num">Lead Time (Days)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations" :key="item.item_sku">
                  <td><strong>{{ item.item_sku }}</strong></td>
                  <td>
                    {{ item.item_name }}
                    <!-- fully_covered === false means the budget funded only part of this shortfall -->
                    <span v-if="item.fully_covered === false" class="badge warning partial-badge">Partial</span>
                  </td>
                  <td>{{ item.category }}</td>
                  <td class="num">{{ item.quantity_on_hand }}</td>
                  <td class="num">{{ item.forecasted_demand }}</td>
                  <td class="num">{{ item.shortfall }}</td>
                  <td class="num"><strong>{{ item.recommended_quantity }}</strong></td>
                  <td class="num">{{ formatUsdExact(item.unit_cost) }}</td>
                  <td class="num"><strong>{{ formatUsdExact(item.line_total) }}</strong></td>
                  <td class="num">{{ item.lead_time_days }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="skippedCount > 0" class="skipped-note">
            <!-- Badge carries the meaning as a word, so the warning survives a
                 colourblind reader and a greyscale screenshot. -->
            <span class="badge warning">Over budget</span>
            {{ skippedCount }} additional {{ skippedCount === 1 ? 'item' : 'items' }} with a shortfall could not be covered by this budget.
          </p>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../api'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Slider bounds. Full coverage of today's shortfalls costs roughly $29,400,
// so the range extends well past that to allow headroom.
const BUDGET_MIN = 0
const BUDGET_MAX = 50000
const BUDGET_STEP = 500
const DEFAULT_BUDGET = 10000
const FULL_COVERAGE_ESTIMATE = 29400
const DEBOUNCE_MS = 300

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(DEFAULT_BUDGET)
    const plan = ref(null)

    const loading = ref(true)
    const error = ref(null)

    const submitting = ref(false)
    const submitError = ref(null)
    const placedOrder = ref(null)

    // Derived values from the last successful recommendations response
    const recommendations = computed(() => plan.value?.items || [])
    const totalCost = computed(() => plan.value?.total_cost || 0)
    const remainingBudget = computed(() => plan.value?.remaining_budget || 0)
    const skippedCount = computed(() => plan.value?.skipped_count || 0)
    const appliedBudget = computed(() =>
      plan.value ? plan.value.budget : budget.value
    )

    const canPlaceOrder = computed(
      () => recommendations.value.length > 0 && !submitting.value
    )

    // This tab intentionally stays USD/English even in Japanese mode (matches Reports).
    const formatUsd = (value) => formatCurrency(value || 0, 'USD')

    // Money that has to reconcile - unit costs, line totals and the plan total - keeps its
    // cents. formatCurrency() rounds to whole dollars, which makes a column of lines look
    // like it does not add up to its total.
    const formatUsdExact = (value) => formatCurrencyWithDecimals(value || 0, 'USD', 2)

    // Restock dates are date-only (YYYY-MM-DD). new Date() reads those as UTC midnight,
    // which renders as the previous day in any timezone behind UTC, so build a local date.
    const formatDate = (dateString) => {
      const [year, month, day] = String(dateString).split('-').map(Number)
      if (!year || !month || !day) return dateString
      return new Date(year, month - 1, day).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        plan.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value =
          err.response?.data?.detail || 'Failed to load restock recommendations'
        console.error('Restock recommendations error:', err)
      } finally {
        loading.value = false
      }
    }

    // Debounce the slider with a plain setTimeout handle so dragging it does not
    // fire a request per step (@vueuse/core is not a dependency of this project).
    let debounceHandle = null
    watch(budget, () => {
      // A new budget invalidates the previous confirmation/error banner.
      placedOrder.value = null
      submitError.value = null
      if (debounceHandle) clearTimeout(debounceHandle)
      debounceHandle = setTimeout(() => {
        debounceHandle = null
        loadRecommendations()
      }, DEBOUNCE_MS)
    })

    onUnmounted(() => {
      if (debounceHandle) clearTimeout(debounceHandle)
    })

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      try {
        submitting.value = true
        submitError.value = null
        placedOrder.value = null
        // The server re-prices the order, so only SKU and quantity are sent.
        const items = recommendations.value.map((item) => ({
          item_sku: item.item_sku,
          quantity: item.recommended_quantity
        }))
        placedOrder.value = await api.createRestockOrder(budget.value, items)
        // Submitting does not change stock on hand - the goods arrive later - so the
        // refreshed plan is expected to look the same until delivery.
        await loadRecommendations()
      } catch (err) {
        submitError.value =
          err.response?.data?.detail || 'Failed to place restock order'
        console.error('Place restock order error:', err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      FULL_COVERAGE_ESTIMATE,
      budget,
      loading,
      error,
      submitting,
      submitError,
      placedOrder,
      recommendations,
      totalCost,
      remainingBudget,
      skippedCount,
      appliedBudget,
      canPlaceOrder,
      formatUsd,
      formatUsdExact,
      formatDate,
      placeOrder
    }
  }
}
</script>

<style scoped>
/* What's left here is genuinely specific to this view: the budget slider, the
   success confirmation banner, and two small spacing rules. Cards, the page
   header, stat tiles, the table, badges, buttons and the loading/empty/error
   states all come from styles/primitives.css now. */

.budget-control {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.budget-bound {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* Range inputs can't be styled through the shared .input primitive - they need
   the vendor track/thumb pseudo-elements, so the geometry below is real
   view-specific geometry rather than a duplicated primitive. */
.budget-slider {
  flex: 1;
  height: 6px;
  appearance: none;
  -webkit-appearance: none;
  background: var(--color-border);
  border-radius: var(--radius-pill);
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid var(--color-surface);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid var(--color-surface);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}

.budget-slider:focus-visible {
  box-shadow: var(--focus-ring);
}

.budget-hint {
  margin-top: var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* No success banner in the primitives layer yet - .state--error is the only
   toned variant - so this one stays local, built from the status tokens. */
.confirmation {
  background: var(--success-bg);
  border: 1px solid var(--success-border);
  color: var(--success-fg);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-5);
}

.confirmation-title {
  font-weight: var(--weight-semibold);
  font-size: var(--text-base);
  margin-bottom: var(--space-1);
}

.confirmation-details {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  font-size: var(--text-sm);
}

/* The inline error banners sit between cards, so they need the same rhythm. */
.state--error {
  margin-bottom: var(--space-5);
}

.partial-badge {
  margin-left: var(--space-2);
  vertical-align: middle;
}

.skipped-note {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-4);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
</style>
