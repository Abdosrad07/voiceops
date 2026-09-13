import { memo } from 'react'

import type { TranscriptItem } from '../hooks/useVoiceAgent'

interface TranscriptPanelProps {
  items: TranscriptItem[]
}

function TranscriptPanelInner({ items }: TranscriptPanelProps) {
  return (
    <section className="panel" aria-label="Conversation" aria-live="polite">
      <h2>Conversation</h2>
      {items.length === 0 ? (
        <p className="muted">Aucun échange pour le moment.</p>
      ) : (
        <ul className="transcript">
          {items.map((item, index) => (
            <li key={index} className={`turn turn-${item.role}`}>
              <span className="who">{item.role === 'user' ? 'Vous' : 'VoiceOps'}</span>
              <p>{item.text}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export const TranscriptPanel = memo(TranscriptPanelInner)