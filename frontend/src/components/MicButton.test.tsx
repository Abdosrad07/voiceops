import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'

import { MicButton } from './MicButton'

it('affiche Parler et déclenche le toggle', async () => {
  const onToggle = vi.fn()
  const user = userEvent.setup()
  render(<MicButton active={false} supported onToggle={onToggle} />)

  const button = screen.getByRole('button', { name: /écoute vocale/i })
  await user.click(button)
  expect(onToggle).toHaveBeenCalledTimes(1)
})

it('affiche Arrêter quand actif', () => {
  render(<MicButton active supported onToggle={() => undefined} />)
  expect(
    screen.getByRole('button', { name: /arrêter .*écoute vocale/i }),
  ).toBeInTheDocument()
})

it('est désactivé quand le micro n’est pas supporté', () => {
  render(<MicButton active={false} supported={false} onToggle={() => undefined} />)
  expect(screen.getByRole('button')).toBeDisabled()
})