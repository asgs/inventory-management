import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock localStorage before importing the composable
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
}
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

import { useI18n } from '../composables/useI18n.js'

describe('useI18n', () => {
  beforeEach(() => {
    const { setLocale } = useI18n()
    setLocale('en')
    vi.clearAllMocks()
  })

  it('defaults to English locale', () => {
    const { currentLocale } = useI18n()

    expect(currentLocale.value).toBe('en')
  })

  it('t() returns English translations', () => {
    const { t } = useI18n()

    expect(t('nav.overview')).toBe('Overview')
    expect(t('nav.inventory')).toBe('Inventory')
    expect(t('nav.orders')).toBe('Orders')
  })

  it('switches locale to Japanese', () => {
    const { setLocale, currentLocale } = useI18n()

    setLocale('ja')

    expect(currentLocale.value).toBe('ja')
  })

  it('t() returns Japanese translations after switching locale', () => {
    const { t, setLocale } = useI18n()

    setLocale('ja')

    expect(t('nav.overview')).toBe('概要')
    expect(t('nav.inventory')).toBe('在庫')
    expect(t('nav.orders')).toBe('注文')
  })

  it('falls back to key when translation is missing', () => {
    const { t } = useI18n()

    expect(t('nonexistent.key')).toBe('nonexistent.key')
  })

  it('falls back to key for missing translation in Japanese', () => {
    const { t, setLocale } = useI18n()

    setLocale('ja')

    expect(t('completely.missing.key')).toBe('completely.missing.key')
  })

  it('setLocale saves to localStorage', () => {
    const { setLocale } = useI18n()

    setLocale('ja')

    expect(localStorageMock.setItem).toHaveBeenCalledWith('app-locale', 'ja')
  })

  it('does not switch to unsupported locale', () => {
    const { setLocale, currentLocale } = useI18n()

    setLocale('fr')

    expect(currentLocale.value).not.toBe('fr')
  })

  it('currentCurrency returns USD for English locale', () => {
    const { currentCurrency } = useI18n()

    expect(currentCurrency.value).toBe('USD')
  })

  it('currentCurrency returns JPY for Japanese locale', () => {
    const { setLocale, currentCurrency } = useI18n()

    setLocale('ja')

    expect(currentCurrency.value).toBe('JPY')
  })
})
