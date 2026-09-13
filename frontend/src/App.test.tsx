import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from './services/api'
import App from './App'

vi.mock('./services/api', () => ({
  api: {
    listIncidents: vi.fn(),
  },
}))

const INCIDENT = {
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
}

describe('App', () => {
  beforeEach(() => {
    vi.mocked(api.listIncidents).mockResolvedValue({
      items: [INCIDENT],
      total: 1,
      limit: 50,
      offset: 0,
    })
  })

  it('rend la barre supérieure et le titre', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /voiceops/i })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /écoute vocale/i }),
    ).toBeInTheDocument()
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

  it('filtre par recherche (débounce) avec les paramètres API', async () => {
    render(<App />)
    const input = screen.getByRole('searchbox', { name: /rechercher dans les incidents/i })
    const user = await import('@testing-library/user-event').then((m) => m.default)
    await user.type(input, 'DHCP')
    await screen.findByText(/PC sans réseau/i)
    await vi.waitFor(() => {
      expect(api.listIncidents).toHaveBeenCalledWith(
        expect.objectContaining({ q: 'DHCP', limit: 50 }),
      )
    })
  })
})