import { memo, useCallback, useEffect, useMemo, useState } from 'react'

import { IncidentPanel } from './components/IncidentPanel'
import { MicButton } from './components/MicButton'
import { RecordBar } from './components/RecordBar'
import { StatusBadge } from './components/StatusBadge'
import { ToolCallList } from './components/ToolCallList'
import { TranscriptPanel } from './components/TranscriptPanel'
import { useVoiceAgent } from './hooks/useVoiceAgent'
import { api } from './services/api'
import type { Incident, IncidentFilters } from './services/api'
import { useDebounce } from './utils/useDebounce'
import './App.css'

const PAGE_SIZE = 50

function App() {
  const { status, transcript, toolCalls, start, stop, supported } = useVoiceAgent()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [incidentsTotal, setIncidentsTotal] = useState(0)
  const [incidentsLoading, setIncidentsLoading] = useState(true)
  const [searchRaw, setSearchRaw] = useState('')
  const searchValue = useDebounce(searchRaw, 300)

  const fetchIncidents = useCallback(
  async (filters: IncidentFilters | undefined) => {
    const response = await api.listIncidents({ limit: PAGE_SIZE, ...filters })
    return response
  },
  [],
)

useEffect(() => {
  let cancelled = false
  async function load() {
    try {
      const response = await fetchIncidents(searchValue ? { q: searchValue } : undefined)
      if (!cancelled) {
        setIncidents(response.items)
        setIncidentsTotal(response.total)
      }
    } catch {
      if (!cancelled) {
        setIncidents([])
        setIncidentsTotal(0)
      }
    } finally {
      if (!cancelled) setIncidentsLoading(false)
    }
  }
  void load()
  return () => {
    cancelled = true
  }
}, [fetchIncidents, searchValue])

const active =
    status === 'listening' || status === 'starting' || status === 'speaking'
  const handleToggle = useCallback(() => {
    if (active) stop()
    else void start()
  }, [active, start, stop])

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (
        event.code !== 'Space' ||
        event.ctrlKey ||
        event.metaKey ||
        event.altKey
      )
        return
      const target = event.target as HTMLElement
      const tag = target.tagName.toLowerCase()
      if (tag === 'input' || tag === 'textarea' || tag === 'select' || target.isContentEditable)
        return
      event.preventDefault()
      handleToggle()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleToggle])

  const headerStatus = useMemo(() => status, [status])

  return (
    <div className="app" role="application" aria-label="VoiceOps – assistant vocal">
      <header className="topbar">
        <h1>VoiceOps</h1>
        <StatusBadge status={headerStatus} />
        <MicButton active={active} supported={supported} onToggle={handleToggle} />
      </header>

      <RecordBar active={status === 'listening'} />

      {!supported && (
        <p className="notice" role="alert">
          La capture micro n'est pas disponible ici (utilisez Chrome et un
          microphone) — le tableau de bord reste consultable.
        </p>
      )}

      <main className="grid">
        <TranscriptPanel items={transcript} />
        <ToolCallList items={toolCalls} />
        <IncidentPanel
          incidents={incidents}
          loading={incidentsLoading}
          searchTerm={searchRaw}
          onSearchChange={setSearchRaw}
        />
      </main>

      <footer className="app-footer muted" aria-label="Informations de session">
        {incidentsTotal > 0 && (
          <span>{incidentsTotal} incident{incidentsTotal > 1 ? 's' : ''}</span>
        )}
      </footer>
    </div>
  )
}

export default memo(App)