import type { ToolCallItem } from '../hooks/useVoiceAgent'

interface ToolCallListProps {
  items: ToolCallItem[]
}

export function ToolCallList({ items }: ToolCallListProps) {
  return (
    <section className="panel" aria-label="Appels d'outils">
      <h2>Outils exécutés</h2>
      {items.length === 0 ? (
        <p className="muted">Aucun appel d’outil.</p>
      ) : (
        <ul className="toolcalls">
          {items.map((item, index) => (
            <li key={index}>
              <span className={`tool-status tool-status-${item.status}`} />
              <code>{item.name}</code>
              <span className="muted">{item.status}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}