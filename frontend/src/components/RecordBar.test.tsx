import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'

import { RecordBar } from './RecordBar'

it('est masqué quand inactif', () => {
  const { container } = render(<RecordBar active={false} />)
  const bar = container.querySelector('.record-bar')
  expect(bar).not.toBeNull()
  expect(bar?.classList.contains('record-bar-active')).toBe(false)
  expect(bar?.getAttribute('aria-hidden')).toBe('true')
})

it('affiche le message quand actif', () => {
  const { container } = render(<RecordBar active />)
  const bar = container.querySelector('.record-bar')
  expect(bar?.classList.contains('record-bar-active')).toBe(true)
  expect(bar?.getAttribute('aria-hidden')).toBe('false')
  expect(screen.getByText(/micro actif — parlez/i)).toBeInTheDocument()
})