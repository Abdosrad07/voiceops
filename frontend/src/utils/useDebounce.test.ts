import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useDebounce, useDebouncedCallback } from './useDebounce'

describe('useDebounce', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('réinitialise le délai à chaque changement rapide', () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: 'a' },
    })
    rerender({ value: 'b' })
    rerender({ value: 'c' })
    act(() => vi.advanceTimersByTime(200))
    expect(result.current).toBe('a') // délai repoussé à la dernière valeur
    act(() => vi.advanceTimersByTime(150))
    expect(result.current).toBe('c')
  })
})

describe('useDebouncedCallback', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('retarde l’appel jusqu’au délai', () => {
    const spy = vi.fn()
    const { result } = renderHook(() => useDebouncedCallback(spy, 250))

    act(() => result.current('x'))
    expect(spy).not.toHaveBeenCalled()
    act(() => vi.advanceTimersByTime(250))
    expect(spy).toHaveBeenCalledWith('x')
    expect(spy).toHaveBeenCalledTimes(1)
  })

  it('réinitialise le délai si appelé de nouveau', () => {
    const spy = vi.fn()
    const { result } = renderHook(() => useDebouncedCallback(spy, 200))

    act(() => result.current('1'))
    act(() => vi.advanceTimersByTime(100))
    act(() => result.current('2'))
    act(() => vi.advanceTimersByTime(200))
    expect(spy).toHaveBeenCalledWith('2')
    expect(spy).toHaveBeenCalledTimes(1)
  })
})