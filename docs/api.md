# VoiceOps — Référence API

Base : `http://localhost:8000` (docs Swagger : `/docs`). Format : JSON.

## Santé

### `GET /`
- 200 `{ "status": "ok", "app": "voiceops", "version": "0.1.0" }`

### `GET /api/health`
- 200 `{ "status": "ok" }`

## Diagnostic réseau

### `GET /api/diagnostics/devices`
Liste des équipements simulés.
- 200 : `[{ "name": "PC-B204", "type": "PC", "ip": "169.254.14.23", "vlan": 10, ... }]`

### `GET /api/diagnostics/scenarios`
Scénarios de panne préconfigurés.

### `GET /api/diagnostics/device/{name}`
Fiche d'un équipement. 404 si inconnu.

### `GET /api/diagnostics/device/{name}/diagnosis`
Diagnostic complet (IP, VLAN, DHCP, DNS, passerelle, actions recommandées).
- 200 : `{ "device": "PC-B204", "nb_issues": 2, "root_cause": "...", ... }`

### `GET /api/diagnostics/device/{name}/{tool}`
Un outil isolé : `ip`, `vlan`, `dhcp`, `dns`, `gateway`, `ping`, `traceroute`, `status`.

## Incidents

### `POST /api/incidents`
Créer un incident (statut initial `OPEN`). Corps :
```json
{
  "title": "PC sans réseau",
  "description": "Le PC du bureau 204 n'accède plus au réseau.",
  "device": "PC-B204",
  "category": "Network / VLAN",
  "severity": "medium",
  "diagnosis": "VLAN incorrect",
  "root_cause": "Port sur le VLAN 10 au lieu du VLAN 20"
}
```
- 201 : incident créé (id, status, dates).

### `GET /api/incidents`
Liste (filtres optionnels `status`, `device`).

### `GET /api/incidents/{id}` · `PATCH /api/incidents/{id}`
Détail / mise à jour. Statuts valides : `OPEN`, `INVESTIGATING`, `RESOLVED`, `CLOSED`.

### `GET /api/incidents/{id}/history`
Historique des changements de statut.

## Rapports

### `POST /api/incidents/{id}/report`
Génère le rapport structuré `Incident #VO-xxx` et le stocke. 201.

### `GET /api/reports/{report_id}` · `GET /api/incidents/{id}/reports`
Lecture d'un rapport / liste des rapports d'un incident.

## Voix (AssemblyAI Voice Agent)

### `GET /api/voice-token`
Mint un token temporaire mono-usage + la configuration de session serveur.
- 503 si `ASSEMBLYAI_API_KEY` absente. 502 en cas d'erreur AssemblyAI.
```json
{
  "token": "…",
  "expires_in_seconds": 300,
  "max_session_duration_seconds": 1800,
  "config": { "system_prompt": "…", "greeting": "…", "output": { "voice": "ivy" }, "tools": [ … ] }
}
```

### `POST /api/tools/execute`
Relais navigateur → backend de l'appel d'outil demandé par l'agent.
```json
{ "name": "check_vlan", "call_id": "call_abc", "arguments": { "device": "PC-B204" } }
```
- 200 : résultat de l'outil. 400 : outil inconnu/erreur.

### `POST /api/sessions` · `POST /api/sessions/{id}/end`
Ouverture / clôture d'une session voix (`incident_id` optionnel).

## RAG

Outil agent `search_knowledge` (`POST /api/tools/execute`) : recherche sémantique dans
`knowledge/` (index TF-IDF, `backend/rag_index.json`). Dégradé propre sans index.