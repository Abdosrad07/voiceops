import { useEffect, useRef, useState } from 'react'

export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(id)
  }, [value, delay])

  return debounced
}

export function useDebouncedCallback<T extends (...args: never[]) => void>(
  callback: T,
  delay = 300,
): T {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (timer.current) window.clearTimeout(timer.current)
    }
  }, [])

  return ((...args: Parameters<T>) => {
    if (timer.current) window.clearTimeout(timer.current)
    timer.current = setTimeout(() => callback(...args), delay)
  }) as T
}