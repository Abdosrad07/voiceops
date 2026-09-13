# VoiceOps — Architecture

## Vue d'ensemble

```
React (Vite, TS)   ────HTTP────▶   FastAPI (Python 3.12)
     │                                  │
     │ GET /api/voice-token             ├── SQLite (SQLAlchemy)
     │                                  ├── simulateur réseau (JSON)
     │                                  ├── RAG (knowledge/ + index TF-IDF)
     ▼                                  │
  WebSocket wss://agents.assemblyai.com/v1/ws  ◀── token temporaire
     │  (24 kHz PCM16, base64)
     ▼
 AssemblyAI Voice Agent (STT → LLM → TTS + tool calling)
```

La clé AssemblyAI **ne quitte jamais le backend** : le navigateur reçoit un
token temporaire mono-usage et s'y connecte directement. Le backend reste le
seul exécuteur des outils (le navigateur relaie `tool.call` via
`POST /api/tools/execute`).

## Modules backend (`backend/app`)

| Module | Rôle |
| --- | --- |
| `main.py` | App FastAPI, lifespan (`init_db` + dispose propre), middlewares, montage des routers. |
| `api/routes/health.py` | `/health` + `/health/deep` (DB, RAG, AssemblyAI). |
| `api/routes/diagnostics.py` | Diagnostic réseau (IP, VLAN, DHCP, DNS, passerelle…). |
| `api/routes/incidents.py` | CRUD incidents paginé/filtrable + workflow de statut strict + audit. |
| `api/routes/reports.py` | Génération et lecture des rapports structurés. |
| `api/routes/voice.py` | `/api/voice-token`, `/api/tools/execute`, sessions (liste paginée). |
| `core/config.py` | Settings (`.env`), `settings` global. |
| `core/security.py` | Clé API (serveur uniquement), assainissement d'entrées. |
| `core/logging.py` | Logs structurés JSON + request-id + `audit_log`. |
| `core/middleware.py` | Headers de sécurité, CORS, rate limiting par IP, logs de requêtes. |
| `core/resilience.py` | Retry exponentiel + circuit breaker (AssemblyAI). |
| `network/` | `simulator.py` (JSON + latence optionnelle), `devices.py`, `diagnostics.py`. |
| `agents/tools.py` | Registry d'outils + `execute_tool_call` (validation stricte, timeout). |
| `agents/prompts.py` | Prompt système VoiceOps (français). |
| `voice/events.py` | Middleware de tool calling, `tool_result_payload`. |
| `voice/assemblyai.py` | Token temporaire (retry + circuit) + config de session. |
| `voice/sessions.py` | Cycle de vie des sessions voix. |
| `rag/` | `embeddings.py` (TF-IDF local), `index.py`, `retriever.py`. |
| `models/` | `Incident`, `Session`, `Report`, `ToolCall`. |

## Données

- `simulator/devices.json` : équipements (adresse, VLAN, état).
- `simulator/topology.json` : liens switch ↔ routeur ↔ serveurs.
- `simulator/scenarios.json` : pannes (VLAN mismatch, DHCP fail, DNS fail…).
- `knowledge/` : base documentaire Markdown (cisco, networking, telecom, troubleshooting).
- `backend/voiceops.db` : SQLite (incidents, sessions, rapports, appels d'outils).

## Modèle de données

- `Incident` : titre, description, équipement, catégorie, sévérité, diagnostic,
  cause probable, statut (`OPEN` → `INVESTIGATING` → `RESOLVED`/`CLOSED`),
  `status_history` (JSON), dates.
- `Session` : session voix liée optionnellement à un incident.
- `Report` : rapport texte généré (lié à un incident).
- `ToolCall` : trace des appels d'outils.

## Flux vocal (tool calling)

1. Le technicien parle ; AssemblyAI transcrit (`transcript.user`).
2. L'agent décide d'un outil → événement `tool.call`.
3. Le navigateur relaie : `POST /api/tools/execute` → `execute_tool_call`.
4. Le résultat est accumulé et renvoyé via `tool.result` **après** `reply.done`
   (jeté si `status: "interrupted"`, barge-in).
5. L'agent conclut, crée l'incident et génère le rapport (`create_incident`,
   `generate_report`).

## Sécurité

- `ASSEMBLYAI_API_KEY` uniquement côté serveur (`.env`, gitignoré).
- Token navigateur : temporaire, mono-usage, généré par le backend.
- Tools : liste blanche dans `agents/tools.py` (jamais de shell/exécution réelle).
  Arguments validés contre le schéma (≤ 5, types/enums) + budget temps.
- Headers de sécurité, CSP, CORS restreinte, rate limiting par IP, gzip > 1 Ko.
- Retry exponentiel (timeouts/5xx) + circuit breaker sur les appels AssemblyAI.
- Logs structurés JSON (request-id) ; audit des incidents/sessions/appels d'outils,
  jamais de données sensibles.
- Le simulateur répond seul : aucun accès aux équipements réels.

## Base de données (SQLite)

- PRAGMAs : `journal_mode=WAL`, `synchronous=NORMAL`, `temp_store=MEMORY`,
  `cache_size=-10000`, `busy_timeout`, `foreign_keys=ON`.
- Pool de connexions : `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`.
- Index : `incidents` (device, category, severity, status, created_at),
  `sessions` (incident_id, started_at), `tool_calls` (session_id, tool_name, created_at).
- Arrêt propre (dispose) via le lifespan FastAPI.