import { memo } from 'react'

import type { Incident } from '../services/api'

interface IncidentPanelProps {
  incidents: Incident[]
  loading: boolean
  searchTerm: string
  onSearchChange: (value: string) => void
}

const SEVERITY_LABEL: Record<string, string> = {
  low: 'Basse',
  medium: 'Moyenne',
  high: 'Haute',
  critical: 'Critique',
}

function IncidentPanelInner({
  incidents,
  loading,
  searchTerm,
  onSearchChange,
}: IncidentPanelProps) {
  return (
    <section className="panel" aria-label="Incidents">
      <h2>Incidents</h2>
      <input
        className="search"
        type="search"
        placeholder="Rechercher (titre, description…)"
        aria-label="Rechercher dans les incidents"
        maxLength={255}
        value={searchTerm}
        onChange={(event) => onSearchChange(event.target.value)}
      />
      {loading ? (
        <p className="muted">Chargement…</p>
      ) : incidents.length === 0 ? (
        <p className="muted">Aucun incident enregistré.</p>
      ) : (
        <ul className="incidents" aria-live="polite">
          {incidents.map((incident) => (
            <li key={incident.id} className="incident">
              <header>
                <code>#{incident.id}</code>
                <span className={`severity severity-${incident.severity}`}>
                  {SEVERITY_LABEL[incident.severity] ?? incident.severity}
                </span>
                <span className={`status status-${incident.status.toLowerCase()}`}>
                  {incident.status}
                </span>
              </header>
              <h3>{incident.title}</h3>
              {incident.device && <p className="muted">Équipement : {incident.device}</p>}
              {incident.root_cause && <p className="root-cause">{incident.root_cause}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export const IncidentPanel = memo(IncidentPanelInner)