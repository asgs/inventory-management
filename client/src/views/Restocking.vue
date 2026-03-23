<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-body">
        <div class="budget-display">
          {{ currencySymbol }}{{ budget.toLocaleString() }}
        </div>
        <input
          type="range"
          min="1000"
          max="1000000"
          step="1000"
          v-model.number="budget"
          class="budget-slider"
          aria-label="Restocking budget"
        />
        <div class="slider-labels">
          <span>{{ currencySymbol }}1,000</span>
          <span>{{ currencySymbol }}1,000,000</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading" aria-live="polite" role="status">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error" role="alert">{{ error }}</div>
    <div v-else-if="recommendations">

      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.itemsToRestock') }}</div>
          <div class="stat-value">{{ recommendations.items_included }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ recommendations.total_cost.toLocaleString() }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ (budget - recommendations.total_cost).toLocaleString() }}</div>
        </div>
      </div>

      <div v-if="orderPlaced" class="order-success">
        {{ t('restocking.orderSuccess', { orderNumber: orderPlaced.order_number, date: orderPlaced.expected_delivery }) }}
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.items.length }})</h3>
        </div>

        <div v-if="recommendations.items.length === 0" class="no-recommendations">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table class="restocking-table" aria-label="Restocking recommendations">
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.restockCost') }}</th>
                <th>{{ t('restocking.table.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations.items"
                :key="item.item_sku"
                :class="{ 'row-muted': !item.included }"
              >
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.demand_gap.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ item.restock_cost.toLocaleString() }}</td>
                <td>
                  <span v-if="item.included" class="badge success" role="status">Included</span>
                  <span v-else class="text-muted">{{ t('restocking.excluded') }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="recommendations.items_included > 0" class="place-order-row">
          <button
            class="place-order-btn"
            :disabled="placingOrder || !!orderPlaced"
            @click="placeOrder"
          >
            {{ placingOrder ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(50000)
    const recommendations = ref(null)
    const loading = ref(false)
    const error = ref(null)
    const orderPlaced = ref(null)
    const placingOrder = ref(false)

    // Debounce timer handle
    let debounceTimer = null

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        const result = await api.getRestockingRecommendations(budget.value)
        recommendations.value = result
      } catch (err) {
        error.value = 'Failed to load restocking recommendations'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    // Watch budget with manual debounce (300ms)
    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    })

    const placeOrder = async () => {
      if (!recommendations.value || placingOrder.value || orderPlaced.value) return

      placingOrder.value = true
      error.value = null
      try {
        const includedItems = recommendations.value.items
          .filter(item => item.included)
          .map(item => ({
            sku: item.item_sku,
            name: item.item_name,
            quantity: item.demand_gap,
            unit_price: item.unit_cost
          }))

        const result = await api.createRestockingOrder({
          items: includedItems,
          budget: budget.value
        })
        orderPlaced.value = result
      } catch (err) {
        error.value = 'Failed to place restocking order'
        console.error(err)
      } finally {
        placingOrder.value = false
      }
    }

    onMounted(() => loadRecommendations())

    onUnmounted(() => {
      clearTimeout(debounceTimer)
    })

    return {
      t,
      currencySymbol,
      budget,
      recommendations,
      loading,
      error,
      orderPlaced,
      placingOrder,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.budget-body {
  padding: 1rem 0 0.5rem;
}

.budget-display {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 1.25rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
  accent-color: #3b82f6;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(59, 130, 246, 0.4);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.5);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(59, 130, 246, 0.4);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.no-recommendations {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.order-success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

.row-muted {
  opacity: 0.6;
}

.text-muted {
  color: #94a3b8;
  font-size: 0.813rem;
}

.place-order-row {
  padding: 1.25rem 0 0.25rem;
  display: flex;
  justify-content: flex-end;
}

.place-order-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
