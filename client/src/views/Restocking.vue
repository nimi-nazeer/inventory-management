<template>
  <div class="restocking">
    <div class="page-header">
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-control">
        <div class="budget-readout">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        <input
          v-model.number="budget"
          class="budget-slider"
          type="range"
          :min="BUDGET_MIN"
          :max="BUDGET_MAX"
          :step="BUDGET_STEP"
          :aria-label="t('restocking.budget')"
        />
        <div class="budget-scale">
          <span>{{ currencySymbol }}{{ BUDGET_MIN.toLocaleString() }}</span>
          <span>{{ currencySymbol }}{{ BUDGET_MAX.toLocaleString() }}</span>
        </div>
        <p class="budget-help">{{ t('restocking.budgetHelp') }}</p>
      </div>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="loading && rows.length === 0" class="loading">{{ t('common.loading') }}</div>

    <template v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.orderTotal') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ orderTotal.toLocaleString() }}</div>
        </div>
        <div :class="['stat-card', overBudget ? 'danger' : 'success']">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ t('orders.leadTimeDays', { count: longestLeadTime }) }}</div>
        </div>
      </div>

      <div v-if="overBudget" class="warning-banner">{{ t('restocking.overBudget') }}</div>
      <div v-if="success" class="success-banner">
        {{ t('restocking.orderPlaced', { number: success.number, days: success.days }) }}
        <router-link to="/orders" class="view-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ rows.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="!canSubmit"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="rows.length === 0" class="empty">{{ t('restocking.noRecommendations') }}</div>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-growth">{{ t('restocking.table.growth') }}</th>
                <th class="col-num">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-qty">{{ t('restocking.table.quantity') }}</th>
                <th class="col-num">{{ t('restocking.table.lineCost') }}</th>
                <th class="col-lead">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.sku">
                <td class="col-sku"><strong>{{ row.sku }}</strong></td>
                <td class="col-name">{{ row.name }}</td>
                <td class="col-growth">
                  <span :class="['badge', row.growth_percent >= 0 ? 'success' : 'danger']">
                    {{ row.growth_percent > 0 ? '+' : '' }}{{ row.growth_percent }}%
                  </span>
                </td>
                <td class="col-num">{{ currencySymbol }}{{ row.unit_cost.toLocaleString() }}</td>
                <td class="col-qty">
                  <input
                    class="qty-input"
                    type="number"
                    min="0"
                    step="1"
                    :max="row.max_quantity"
                    :value="row.quantity"
                    @input="onQuantityInput(row, $event)"
                    @blur="onQuantityBlur(row, $event)"
                  />
                  <span class="qty-max">/ {{ row.max_quantity }}</span>
                </td>
                <td class="col-num"><strong>{{ currencySymbol }}{{ (row.quantity * row.unit_cost).toLocaleString() }}</strong></td>
                <td class="col-lead">{{ t('orders.leadTimeDays', { count: row.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const BUDGET_MIN = 0
    const BUDGET_MAX = 20000
    const BUDGET_STEP = 250

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

    const budget = ref(5000)
    const rows = ref([])
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const success = ref(null)

    let debounceTimer = null
    let requestId = 0

    const clampQty = (value, max) => {
      const n = Math.floor(Number(value))
      if (!Number.isFinite(n)) return 0
      return Math.min(Math.max(n, 0), max)
    }

    const loadRecommendations = async () => {
      const myId = ++requestId
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockRecommendations(budget.value)
        if (myId !== requestId) return // stale response
        rows.value = (data.items || []).map(item => ({ ...item }))
      } catch (err) {
        if (myId !== requestId) return
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        if (myId === requestId) loading.value = false
      }
    }

    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 300)
    })

    const onQuantityInput = (row, event) => {
      const raw = event.target.value
      if (raw === '') {
        row.quantity = 0
        return
      }
      row.quantity = clampQty(raw, row.max_quantity)
    }

    const onQuantityBlur = (row, event) => {
      // Normalize what is displayed (e.g. empty or out-of-range text)
      event.target.value = row.quantity
    }

    const orderTotal = computed(() =>
      rows.value.reduce((sum, r) => sum + r.quantity * r.unit_cost, 0)
    )
    const remainingBudget = computed(() => budget.value - orderTotal.value)
    const overBudget = computed(() => orderTotal.value > budget.value)
    const selectedRows = computed(() => rows.value.filter(r => r.quantity > 0))
    const longestLeadTime = computed(() =>
      selectedRows.value.reduce((max, r) => Math.max(max, r.lead_time_days), 0)
    )
    const canSubmit = computed(
      () => selectedRows.value.length > 0 && !overBudget.value && !submitting.value
    )

    const placeOrder = async () => {
      if (!canSubmit.value) return
      submitting.value = true
      submitError.value = null
      success.value = null
      try {
        const result = await api.createRestockOrder({
          budget: budget.value,
          items: selectedRows.value.map(r => ({ sku: r.sku, quantity: r.quantity }))
        })
        success.value = { number: result.order_number, days: result.lead_time_days }
        await loadRecommendations()
      } catch (err) {
        submitError.value = t('restocking.failed') + (err.response?.data?.detail || err.message)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    onBeforeUnmount(() => {
      clearTimeout(debounceTimer)
      requestId++ // invalidate any in-flight request
    })

    return {
      t,
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      currencySymbol,
      budget,
      rows,
      loading,
      error,
      submitting,
      submitError,
      success,
      orderTotal,
      remainingBudget,
      overBudget,
      longestLeadTime,
      canSubmit,
      onQuantityInput,
      onQuantityBlur,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-control {
  padding: var(--space-2) 0 var(--space-1);
}

.budget-readout {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: var(--space-3);
}

.budget-slider {
  width: 100%;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.budget-help {
  margin-top: var(--space-2);
  font-size: var(--text-base);
  color: var(--text-muted);
}

.warning-banner,
.success-banner {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
  font-size: var(--text-base);
  font-weight: 500;
}

.warning-banner {
  background: #fef2f2;
  border: 1px solid var(--danger-bg);
  color: #b91c1c;
}

.success-banner {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.view-link {
  margin-left: var(--space-2);
  color: var(--primary);
  font-weight: 600;
  text-decoration: underline;
}

.place-order-btn {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-5);
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--primary);
}

.place-order-btn:disabled {
  background: var(--border-strong);
  cursor: not-allowed;
}

.empty {
  padding: var(--space-7);
  text-align: center;
  color: var(--text-muted);
}

.restock-table {
  table-layout: fixed;
  width: 100%;
}

.col-sku { width: 110px; }
.col-name { width: 220px; }
.col-growth { width: 130px; }
.col-num { width: 120px; }
.col-qty { width: 160px; }
.col-lead { width: 110px; }

.qty-input {
  width: 80px;
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  color: var(--text);
}

.qty-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.qty-max {
  margin-left: var(--space-1);
  font-size: var(--text-sm);
  color: var(--text-muted);
}
</style>
