import { useEffect, useState } from 'react'

import { IncidentPanel } from './components/IncidentPanel'
import { MicButton } from './components/MicButton'
import { StatusBadge } from './components/StatusBadge'
import { ToolCallList } from './components/ToolCallList'
import { TranscriptPanel } from './components/TranscriptPanel'
import { useVoiceAgent } from './hooks/useVoiceAgent'
import { api } from './services/api'
import type { Incident } from './services/api'
import './App.css'

function App() {
  const { status, transcript, toolCalls, start, stop, supported } = useVoiceAgent()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [incidentsLoading, setIncidentsLoading] = useState(true)

  useEffect(() => {
    api
      .listIncidents()
      .then(setIncidents)
      .catch(() => setIncidents([]))
      .finally(() => setIncidentsLoading(false))
  }, [])

  const active =
    status === 'listening' || status === 'starting' || status === 'speaking'
  const handleToggle = () => {
    if (active) stop()
    else void start()
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>VoiceOps</h1>
        <StatusBadge status={status} />
        <MicButton active={active} supported={supported} onToggle={handleToggle} />
      </header>

      {!supported && (
        <p className="notice">
          La capture micro n’est pas disponible ici (utilisez Chrome et un
          microphone) — le tableau de bord reste consultable.
        </p>
      )}

      <main className="grid">
        <TranscriptPanel items={transcript} />
        <ToolCallList items={toolCalls} />
        <IncidentPanel incidents={incidents} loading={incidentsLoading} />
      </main>
    </div>
  )
}

export default App