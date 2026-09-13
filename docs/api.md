# VoiceOps — Référence API

Base : `http://localhost:8000` (docs Swagger : `/docs`). Format : JSON.

## Santé

### `GET /`
- 200 `{ "status": "ok", "app": "voiceops", "version": "0.1.0", "health": "/health", "deep_health": "/health/deep" }`

### `GET /health`
- 200 `{ "status": "ok" }` — sonde basique (toujours OK si le processus répond).

### `GET /health/deep`
Health check détaillé : base de données (SELECT 1), index RAG, configuration AssemblyAI.
- `200 { "status": "ok"|"degraded", "checks": { "database", "rag", "rag_chunks", "assemblyai", "environment" } }`

## Sécurité & middlewares

- Headers de sécurité sur toutes les réponses : `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy` (+ `Strict-Transport-Security` en production).
- `X-Request-ID` sur chaque réponse (reporté dans les logs structurés JSON).
- CORS restreinte aux origines configurées (`CORS_ORIGINS`).
- Compression gzip pour les réponses > 1 Ko.
- Rate limiting par IP : tokens `/api/voice-token` et `/api/tools/*` limités plus strictement (`RATE_LIMIT_VOICE_RPM`), le reste à `RATE_LIMIT_RPM`. Réponse `429` avec `Retry-After`. Désactivable via `RATE_LIMIT_ENABLED=false` (utilisé par les tests).

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
Liste paginée et filtrable (enveloppe) :
```
?limit=50&offset=0                     (limite 1-100, offset >= 0)
&sort_by=created_at|updated_at|severity|id
&sort_dir=asc|desc
&status=OPEN&severity=high&device=PC-B204&category=...
&q=DHCP                                (recherche titre + description)
&created_after=...&created_before=...  (ISO 8601)
```
- 200 : `{ "items": [...], "total": N, "limit": 50, "offset": 0 }`

### `GET /api/incidents/{id}` · `PATCH /api/incidents/{id}`
Détail / mise à jour. Statuts valides : `OPEN`, `INVESTIGATING`, `RESOLVED`, `CLOSED`.
Transitions strictement adjacentes (pas de saut ni de réouverture) : `409` sinon.
`422` si statut inconnu ou validation Pydantic en échec.
Validation serveur : longueurs bornées, `severity` dans `low|medium|high|critical`,
champs texte assainis (anti-injection dans l'interface).

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
Le backend retente avec backoff exponentiel (3 essais max, 1s/2s/4s) sur timeouts
et 5xx, et ouvre un *circuit breaker* (échec rapide + cooldown) si AssemblyAI tombe.
- 503 si `ASSEMBLYAI_API_KEY` absente. 502 en cas d'erreur AssemblyAI (réseau ou circuit ouvert).
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
- Validation stricte : nom en liste blanche, arguments bornés (max 5), types et
enums vérifiés contre le schéma déclaré, budget temps (`TOOL_TIMEOUT_SECONDS`).
- `session_id` optionnel : l'appel est journalisé (audit + table `tool_calls`).
```json
{ "name": "check_vlan", "call_id": "call_abc", "arguments": { "device": "PC-B204" }, "session_id": 1 }
```
- 200 : résultat de l'outil. 400 : outil inconnu, arguments invalides ou dépassement.

### `POST /api/sessions` · `GET /api/sessions` · `POST /api/sessions/{id}/end`
Ouverture / liste (paginée `?limit&offset&sort_dir`) / clôture d'une session voix (`incident_id` optionnel).

## RAG

Outil agent `search_knowledge` (`POST /api/tools/execute`) : recherche sémantique dans
`knowledge/` (index TF-IDF, `backend/rag_index.json`). Dégradé propre sans index.