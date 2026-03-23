import { describe, it, expect, beforeEach } from 'vitest'
import { useFilters } from '../composables/useFilters.js'

describe('useFilters', () => {
  beforeEach(() => {
    // Reset filters before each test
    const { resetFilters } = useFilters()
    resetFilters()
  })

  it('has correct initial default values', () => {
    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus } = useFilters()

    expect(selectedPeriod.value).toBe('all')
    expect(selectedLocation.value).toBe('all')
    expect(selectedCategory.value).toBe('all')
    expect(selectedStatus.value).toBe('all')
  })

  it('allows setting filter values', () => {
    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus } = useFilters()

    selectedPeriod.value = '2025-01'
    selectedLocation.value = 'San Francisco'
    selectedCategory.value = 'Electronics'
    selectedStatus.value = 'Completed'

    expect(selectedPeriod.value).toBe('2025-01')
    expect(selectedLocation.value).toBe('San Francisco')
    expect(selectedCategory.value).toBe('Electronics')
    expect(selectedStatus.value).toBe('Completed')
  })

  it('resetFilters resets all filters to defaults', () => {
    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, resetFilters } = useFilters()

    selectedPeriod.value = '2025-03'
    selectedLocation.value = 'Tokyo'
    selectedCategory.value = 'Sensors'
    selectedStatus.value = 'Pending'

    resetFilters()

    expect(selectedPeriod.value).toBe('all')
    expect(selectedLocation.value).toBe('all')
    expect(selectedCategory.value).toBe('all')
    expect(selectedStatus.value).toBe('all')
  })

  it('hasActiveFilters is false when all filters are default', () => {
    const { hasActiveFilters } = useFilters()

    expect(hasActiveFilters.value).toBe(false)
  })

  it('hasActiveFilters is true when any filter is set', () => {
    const { selectedCategory, hasActiveFilters } = useFilters()

    selectedCategory.value = 'Electronics'

    expect(hasActiveFilters.value).toBe(true)
  })

  it('hasActiveFilters becomes false after reset', () => {
    const { selectedPeriod, hasActiveFilters, resetFilters } = useFilters()

    selectedPeriod.value = '2025-06'
    expect(hasActiveFilters.value).toBe(true)

    resetFilters()
    expect(hasActiveFilters.value).toBe(false)
  })

  it('getCurrentFilters returns correct filter object', () => {
    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, getCurrentFilters } = useFilters()

    selectedPeriod.value = '2025-01'
    selectedLocation.value = 'London'
    selectedCategory.value = 'Sensors'
    selectedStatus.value = 'Completed'

    const filters = getCurrentFilters()

    expect(filters.warehouse).toBe('London')
    expect(filters.category).toBe('Sensors')
    expect(filters.status).toBe('Completed')
    expect(filters.month).toBe('2025-01')
  })

  it('getCurrentFilters omits month when period is all', () => {
    const { getCurrentFilters } = useFilters()

    const filters = getCurrentFilters()

    expect(filters.month).toBeUndefined()
    expect(filters.warehouse).toBe('all')
    expect(filters.category).toBe('all')
    expect(filters.status).toBe('all')
  })
})
