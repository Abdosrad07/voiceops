import { memo } from 'react'

import type { ToolCallItem } from '../hooks/useVoiceAgent'

interface ToolCallListProps {
  items: ToolCallItem[]
}

function ToolCallListInner({ items }: ToolCallListProps) {
  return (
    <section className="panel" aria-label="Outils exécutés" aria-live="polite">
      <h2>Outils exécutés</h2>
      {items.length === 0 ? (
        <p className="muted">Aucun appel d’outil.</p>
      ) : (
        <ul className="toolcalls">
          {items.map((item, index) => (
            <li key={`${item.name}-${index}`}>
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

export const ToolCallList = memo(ToolCallListInner)