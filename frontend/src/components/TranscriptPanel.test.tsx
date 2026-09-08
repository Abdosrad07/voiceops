import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'

import { TranscriptPanel } from './TranscriptPanel'

it('affiche un message vide par défaut', () => {
  render(<TranscriptPanel items={[]} />)
  expect(screen.getByText(/aucun échange/i)).toBeInTheDocument()
})

it('affiche les tours utilisateur et agent', () => {
  render(
    <TranscriptPanel
      items={[
        { role: 'user', text: 'Le PC 204 n’a plus de réseau' },
        { role: 'agent', text: 'Testons la configuration IP' },
      ]}
    />,
  )
  expect(screen.getByText(/PC 204 n/i)).toBeInTheDocument()
  expect(screen.getByText(/Testons/i)).toBeInTheDocument()
})