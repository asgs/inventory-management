<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close" @keydown.esc="close">
        <div class="modal-container" @click.stop role="dialog" aria-modal="true" aria-labelledby="po-modal-title" ref="modalRef">
          <div class="modal-header">
            <h3 class="modal-title" id="po-modal-title">
              {{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order Details' }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Backlog item context -->
            <div class="item-context">
              <div class="item-context-info">
                <div class="item-name">{{ backlogItem.item_name }}</div>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <div class="item-context-stats">
                <div class="stat-pill danger">
                  Shortage: {{ shortage }} units
                </div>
                <span class="priority-badge" :class="backlogItem.priority">
                  {{ backlogItem.priority }} Priority
                </span>
              </div>
            </div>

            <!-- Create mode: form -->
            <form v-if="mode === 'create'" class="po-form" @submit.prevent="submitForm">
              <div class="form-group">
                <label class="form-label" for="supplier-name">Supplier Name</label>
                <input
                  id="supplier-name"
                  v-model="form.supplier_name"
                  type="text"
                  class="form-input"
                  placeholder="Enter supplier name"
                  required
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="quantity">Quantity</label>
                  <input
                    id="quantity"
                    v-model.number="form.quantity"
                    type="number"
                    class="form-input"
                    min="1"
                    required
                  />
                </div>

                <div class="form-group">
                  <label class="form-label" for="unit-cost">Unit Cost ($)</label>
                  <input
                    id="unit-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    class="form-input"
                    min="0.01"
                    step="0.01"
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label" for="delivery-date">Expected Delivery Date</label>
                <input
                  id="delivery-date"
                  v-model="form.expected_delivery_date"
                  type="date"
                  class="form-input"
                  :min="today"
                  required
                />
              </div>

              <div class="form-group">
                <label class="form-label" for="notes">Notes <span class="optional">(optional)</span></label>
                <textarea
                  id="notes"
                  v-model="form.notes"
                  class="form-textarea"
                  rows="3"
                  placeholder="Additional notes..."
                ></textarea>
              </div>

              <div v-if="totalCost > 0" class="total-cost-preview">
                <span class="total-label">Total Cost</span>
                <span class="total-value">{{ formatCurrency(totalCost) }}</span>
              </div>

              <div v-if="submitError" class="error-message">{{ submitError }}</div>
            </form>

            <!-- View mode: read-only PO details -->
            <div v-else-if="mode === 'view'">
              <div v-if="viewLoading" class="state-message">Loading purchase order...</div>
              <div v-else-if="viewError" class="error-message">{{ viewError }}</div>
              <div v-else-if="poData" class="po-details">
                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">PO ID</div>
                    <div class="info-value mono">{{ poData.id }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Supplier</div>
                    <div class="info-value">{{ poData.supplier_name }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Quantity</div>
                    <div class="info-value">{{ poData.quantity }} units</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Unit Cost</div>
                    <div class="info-value">{{ formatCurrency(poData.unit_cost) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Total Cost</div>
                    <div class="info-value highlight">{{ formatCurrency(poData.unit_cost * poData.quantity) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Expected Delivery</div>
                    <div class="info-value">{{ formatDate(poData.expected_delivery_date) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">
                      <span class="badge" :class="poData.status">{{ poData.status }}</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Created</div>
                    <div class="info-value">{{ formatDate(poData.created_at) }}</div>
                  </div>
                </div>
                <div v-if="poData.notes" class="info-item notes-item">
                  <div class="info-label">Notes</div>
                  <div class="info-value notes-value">{{ poData.notes }}</div>
                </div>
              </div>
              <div v-else class="state-message">No purchase order found.</div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">
              {{ mode === 'create' ? 'Cancel' : 'Close' }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="submitLoading"
              @click="submitForm"
            >
              {{ submitLoading ? 'Creating...' : 'Create Purchase Order' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue'
import { api } from '../api'

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    backlogItem: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create',
      validator: (v) => ['create', 'view'].includes(v)
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    // --- Focus management ---
    const modalRef = ref(null)

    // --- Shared ---
    const today = new Date().toISOString().split('T')[0]

    const defaultDeliveryDate = () => {
      const d = new Date()
      d.setDate(d.getDate() + 14)
      return d.toISOString().split('T')[0]
    }

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
    })

    const formatCurrency = (value) => {
      if (value == null) return 'N/A'
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return 'N/A'
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    }

    const close = () => emit('close')

    // --- Create mode ---
    const form = ref({
      supplier_name: '',
      quantity: 0,
      unit_cost: null,
      expected_delivery_date: defaultDeliveryDate(),
      notes: ''
    })

    const submitLoading = ref(false)
    const submitError = ref(null)

    const totalCost = computed(() => {
      const q = form.value.quantity
      const c = form.value.unit_cost
      if (!q || !c || q <= 0 || c <= 0) return 0
      return q * c
    })

    // Focus first focusable element when modal opens
    watch(() => props.isOpen, (open) => {
      if (open) {
        nextTick(() => {
          const firstFocusable = modalRef.value?.querySelector('button, input, [tabindex]')
          if (firstFocusable) firstFocusable.focus()
        })
      }
    })

    // Reset form when modal opens in create mode
    watch(() => props.isOpen, (open) => {
      if (open && props.mode === 'create') {
        submitError.value = null
        form.value = {
          supplier_name: '',
          quantity: shortage.value > 0 ? shortage.value : 1,
          unit_cost: null,
          expected_delivery_date: defaultDeliveryDate(),
          notes: ''
        }
      }
      if (open && props.mode === 'view') {
        loadPurchaseOrder()
      }
    })

    // Also set quantity when backlogItem changes while modal is open
    watch(() => props.backlogItem, (item) => {
      if (item && props.isOpen && props.mode === 'create') {
        form.value.quantity = item.quantity_needed - item.quantity_available
      }
    })

    const submitForm = async () => {
      if (submitLoading.value) return
      submitError.value = null
      submitLoading.value = true
      try {
        const payload = {
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplier_name,
          quantity: form.value.quantity,
          unit_cost: form.value.unit_cost,
          expected_delivery_date: form.value.expected_delivery_date,
          ...(form.value.notes ? { notes: form.value.notes } : {})
        }
        const result = await api.createPurchaseOrder(payload)
        emit('po-created', result)
        emit('close')
      } catch (err) {
        submitError.value = err?.response?.data?.detail || 'Failed to create purchase order. Please try again.'
        console.error('PO creation error:', err)
      } finally {
        submitLoading.value = false
      }
    }

    // --- View mode ---
    const poData = ref(null)
    const viewLoading = ref(false)
    const viewError = ref(null)

    const loadPurchaseOrder = async () => {
      if (!props.backlogItem) return
      viewLoading.value = true
      viewError.value = null
      poData.value = null
      try {
        poData.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        viewError.value = 'Failed to load purchase order details.'
        console.error('PO load error:', err)
      } finally {
        viewLoading.value = false
      }
    }

    return {
      modalRef,
      today,
      shortage,
      form,
      totalCost,
      submitLoading,
      submitError,
      submitForm,
      poData,
      viewLoading,
      viewError,
      formatCurrency,
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
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem 2rem;
}

/* Item context banner */
.item-context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  margin-bottom: 1.75rem;
  flex-wrap: wrap;
}

.item-name {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.25rem;
}

.item-sku {
  font-size: 0.813rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.item-context-stats {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.stat-pill {
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-size: 0.813rem;
  font-weight: 600;
}

.stat-pill.danger {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.priority-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.priority-badge.high {
  background: #fecaca;
  color: #991b1b;
}

.priority-badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.priority-badge.low {
  background: #dbeafe;
  color: #1e40af;
}

/* Form */
.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.optional {
  font-weight: 400;
  color: #94a3b8;
}

.form-input {
  padding: 0.625rem 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  outline: none;
}

.form-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-textarea {
  padding: 0.625rem 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  outline: none;
}

.form-textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.total-cost-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1.25rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
}

.total-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.total-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #16a34a;
}

/* View mode: PO details */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.notes-item {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
  font-size: 0.875rem;
}

.info-value.highlight {
  color: #16a34a;
  font-weight: 700;
}

.notes-value {
  color: #475569;
  line-height: 1.5;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

.badge.pending {
  background: #fef9c3;
  color: #854d0e;
}

.badge.approved {
  background: #dbeafe;
  color: #1e40af;
}

.badge.ordered {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.received {
  background: #dcfce7;
  color: #166534;
}

.badge.cancelled {
  background: #f1f5f9;
  color: #64748b;
}

/* States */
.state-message {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.error-message {
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Footer */
.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
