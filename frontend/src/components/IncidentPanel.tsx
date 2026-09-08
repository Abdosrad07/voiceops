import type { Incident } from '../services/api'

interface IncidentPanelProps {
  incidents: Incident[]
  loading: boolean
}

const SEVERITY_LABEL: Record<string, string> = {
  low: 'Basse',
  medium: 'Moyenne',
  high: 'Haute',
  critical: 'Critique',
}

export function IncidentPanel({ incidents, loading }: IncidentPanelProps) {
  return (
    <section className="panel" aria-label="Incidents">
      <h2>Incidents</h2>
      {loading ? (
        <p className="muted">Chargement…</p>
      ) : incidents.length === 0 ? (
        <p className="muted">Aucun incident enregistré.</p>
      ) : (
        <ul className="incidents">
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