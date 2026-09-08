import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from './services/api'
import App from './App'

vi.mock('./services/api', () => ({
  api: {
    listIncidents: vi.fn(),
  },
}))

describe('App', () => {
  beforeEach(() => {
    vi.mocked(api.listIncidents).mockResolvedValue([
      {
        id: 1,
        title: 'PC sans réseau',
        description: '',
        device: 'PC-B204',
        category: 'Network',
        severity: 'high',
        diagnosis: '',
        root_cause: 'Mauvais VLAN',
        status: 'OPEN',
        created_at: null,
        updated_at: null,
      },
    ])
  })

  it('rend la barre supérieure et le titre', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /voiceops/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /parler/i })).toBeInTheDocument()
  })

  it('affiche la liste des incidents', async () => {
    render(<App />)
    expect(await screen.findByText(/PC sans réseau/i)).toBeInTheDocument()
    expect(screen.getByText(/Mauvais VLAN/i)).toBeInTheDocument()
  })

  it('affiche les panneaux conversation et outils', () => {
    render(<App />)
    expect(screen.getByText(/Conversation/i)).toBeInTheDocument()
    expect(screen.getByText(/Outils exécutés/i)).toBeInTheDocument()
  })
})