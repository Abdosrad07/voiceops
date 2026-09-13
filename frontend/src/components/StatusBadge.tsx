import type { AgentStatus } from '../hooks/useVoiceAgent'

const LABELS: Record<AgentStatus, string> = {
  idle: 'Prêt',
  starting: 'Connexion…',
  listening: 'À l’écoute',
  speaking: 'Parle',
  error: 'Erreur',
}

interface StatusBadgeProps {
  status: AgentStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={`badge badge-${status}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <span className="dot" aria-hidden="true" /> {LABELS[status]}
    </span>
  )
}