<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container po-modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Backlog item summary (both modes) -->
            <div class="item-summary">
              <div class="summary-row">
                <span class="summary-label">{{ t('purchaseOrder.sku') }}</span>
                <span class="summary-value">{{ backlogItem.item_sku }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">{{ t('purchaseOrder.item') }}</span>
                <span class="summary-value">{{ backlogItem.item_name }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">{{ t('purchaseOrder.shortage') }}</span>
                <span class="summary-value">{{ shortage }}</span>
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loading" class="state-message">{{ t('common.loading') }}</div>
              <div v-else-if="error" class="error-message">{{ error }}</div>
              <div v-else-if="purchaseOrder" class="po-details">
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.poId') }}</span>
                  <span class="summary-value">{{ purchaseOrder.id }}</span>
                </div>
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.supplierName') }}</span>
                  <span class="summary-value">{{ purchaseOrder.supplier_name }}</span>
                </div>
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.quantity') }}</span>
                  <span class="summary-value">{{ purchaseOrder.quantity }}</span>
                </div>
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.unitCost') }}</span>
                  <span class="summary-value">{{ formatMoney(purchaseOrder.unit_cost) }}</span>
                </div>
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.totalCost') }}</span>
                  <span class="summary-value"><strong>{{ formatMoney(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</strong></span>
                </div>
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.expectedDelivery') }}</span>
                  <span class="summary-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</span>
                </div>
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.status') }}</span>
                  <span class="summary-value"><span class="status-badge">{{ purchaseOrder.status }}</span></span>
                </div>
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.createdDate') }}</span>
                  <span class="summary-value">{{ formatDate(purchaseOrder.created_date) }}</span>
                </div>
                <div class="detail-row">
                  <span class="summary-label">{{ t('purchaseOrder.notes') }}</span>
                  <span class="summary-value notes-value">{{ purchaseOrder.notes || t('purchaseOrder.noNotes') }}</span>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" @submit.prevent="handleSubmit">
              <div class="form-group">
                <label for="po-supplier">{{ t('purchaseOrder.supplierName') }}</label>
                <input
                  id="po-supplier"
                  v-model="form.supplier_name"
                  type="text"
                  class="po-input"
                  required
                  :placeholder="t('purchaseOrder.supplierPlaceholder')"
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    min="1"
                    step="1"
                    class="po-input"
                    required
                  />
                </div>
                <div class="form-group">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }}</label>
                  <input
                    id="po-unit-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    min="0.01"
                    step="0.01"
                    class="po-input"
                    required
                  />
                </div>
              </div>

              <div class="form-group">
                <label for="po-delivery">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input
                  id="po-delivery"
                  v-model="form.expected_delivery_date"
                  type="date"
                  class="po-input"
                  required
                />
              </div>

              <div class="form-group">
                <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                <textarea
                  id="po-notes"
                  v-model="form.notes"
                  rows="3"
                  class="po-input"
                  :placeholder="t('purchaseOrder.notesPlaceholder')"
                ></textarea>
              </div>

              <div v-if="error" class="error-message">{{ error }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode !== 'view'"
              type="submit"
              form="po-form"
              class="btn-primary"
              :disabled="!isValid || submitting"
            >
              {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const emptyForm = () => ({
  supplier_name: '',
  quantity: 1,
  unit_cost: null,
  expected_delivery_date: '',
  notes: ''
})

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    },
    backlogItem: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create',
      validator: (value) => ['create', 'view'].includes(value)
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const form = ref(emptyForm())
    const purchaseOrder = ref(null)
    const loading = ref(false)
    const submitting = ref(false)
    const error = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
    })

    const isValid = computed(() => {
      const f = form.value
      return (
        f.supplier_name.trim().length > 0 &&
        Number.isInteger(f.quantity) && f.quantity >= 1 &&
        typeof f.unit_cost === 'number' && f.unit_cost > 0 &&
        !!f.expected_delivery_date
      )
    })

    const getErrorMessage = (err, fallback) => {
      // Surface the backend's detail message when it is a plain string
      const detail = err?.response?.data?.detail
      return typeof detail === 'string' ? detail : fallback
    }

    const loadPurchaseOrder = async () => {
      loading.value = true
      error.value = null
      purchaseOrder.value = null
      const requestedId = props.backlogItem.id
      try {
        const result = await api.getPurchaseOrderByBacklogItem(requestedId)
        // Ignore stale responses if the modal moved on to another item
        if (props.backlogItem?.id === requestedId) purchaseOrder.value = result
      } catch (err) {
        if (props.backlogItem?.id !== requestedId) return
        error.value = getErrorMessage(err, t('purchaseOrder.loadError'))
        console.error('Failed to load purchase order:', err)
      } finally {
        if (props.backlogItem?.id === requestedId) loading.value = false
      }
    }

    // Reset state each time the modal opens or switches to a different item/mode
    watch(
      () => [props.isOpen, props.backlogItem?.id, props.mode],
      ([open]) => {
        if (!open || !props.backlogItem) return
        error.value = null
        submitting.value = false
        if (props.mode === 'view') {
          loadPurchaseOrder()
        } else {
          form.value = { ...emptyForm(), quantity: shortage.value || 1 }
        }
      },
      { immediate: true }
    )

    const handleSubmit = async () => {
      if (!isValid.value || submitting.value) return
      submitting.value = true
      error.value = null
      try {
        const po = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplier_name.trim(),
          quantity: form.value.quantity,
          unit_cost: form.value.unit_cost,
          expected_delivery_date: form.value.expected_delivery_date,
          notes: form.value.notes.trim() || null
        })
        emit('po-created', po)
      } catch (err) {
        error.value = getErrorMessage(err, t('purchaseOrder.createError'))
        console.error('Failed to create purchase order:', err)
      } finally {
        submitting.value = false
      }
    }

    const formatMoney = (value) => {
      const num = Number(value)
      if (isNaN(num)) return '-'
      return num.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    const formatDate = (value) => {
      if (!value) return '-'
      const date = new Date(value)
      if (isNaN(date.getTime())) return value
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const close = () => {
      emit('close')
    }

    return {
      t,
      form,
      purchaseOrder,
      loading,
      submitting,
      error,
      shortage,
      isValid,
      handleSubmit,
      formatMoney,
      formatDate,
      close
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 560px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-6) var(--space-7);
  border-bottom: 2px solid var(--border);
}

.modal-title {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.close-button {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.close-button:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.modal-body {
  padding: var(--space-7);
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: var(--space-6) var(--space-7);
  border-top: 2px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-4);
}

.btn-secondary {
  padding: var(--space-3) var(--space-6);
  background: var(--surface-hover);
  color: #475569;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: var(--border);
}

.btn-primary {
  padding: var(--space-3) var(--space-6);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Item summary and read-only detail rows */
.item-summary,
.po-details {
  background: var(--bg);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  margin-bottom: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.po-details {
  margin-bottom: 0;
}

.summary-row,
.detail-row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-5);
}

.summary-label {
  font-size: var(--text-base);
  font-weight: 600;
  color: #475569;
  flex-shrink: 0;
}

.summary-value {
  color: var(--text);
  text-align: right;
  word-break: break-word;
}

.notes-value {
  white-space: pre-wrap;
}

.status-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  padding: var(--space-1) var(--space-2);
  border-radius: 4px;
  background: var(--info-bg);
  color: var(--info-text);
}

/* Form */
.po-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-row {
  display: flex;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1;
}

label {
  font-size: var(--text-base);
  font-weight: 600;
  color: #475569;
}

.po-input {
  padding: var(--space-3);
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  transition: border-color 0.2s ease;
  font-family: inherit;
  resize: vertical;
}

.po-input:focus {
  outline: none;
  border-color: #667eea;
}

.state-message {
  text-align: center;
  padding: var(--space-7);
  color: var(--text-muted);
}

.error-message {
  padding: var(--space-3) var(--space-4);
  background: var(--danger-bg);
  color: var(--danger-text);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}
</style>
