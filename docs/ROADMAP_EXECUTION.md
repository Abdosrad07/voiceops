# Plan d'exécution VoiceOps — Hackathon 2026

Ce document est le **fil conducteur** d'un agent IA (ou d'un développeur) pour réaliser le MVP VoiceOps sans se perdre. Il transforme la roadmap du `README.md` en tâches concrètes, ordonnées, vérifiables.

> **Cible du MVP** : le scénario de démo suivant doit fonctionner de bout en bout — *« The PC has no network »* → questions de l'agent → récupération IP → check DHCP → check VLAN → cause identifiée → explication orale → rapport d'incident généré.

---

## 1. Règles d'or (à respecter à chaque étape)

1. **Une étape à la fois.** Ne jamais commencer une phase si la précédente n'est pas 100 % validée.
2. **Chaque étape se termine par une vérification** (tests / lint / build). Ne rien marquer « fait » sans preuve.
3. **Rien de réel.** Le MVP ne touche JAMAIS à du matériel réseau réel : tout passe par le simulateur (`simulator/*.json`).
4. **Sécurité : la clé AssemblyAI reste uniquement côté serveur** (`backend/.env`, ignoré par Git). Le navigateur ne reçoit qu'un *temporary token*.
5. **Le LLM ne peut jamais exécuter de commande système arbitraire** (`cmd.exe`, `PowerShell`, `bash`, CLI Cisco). Les outils sont des fonctions Python à accès blanc-liste.
6. **Conventions Git** : branches `feature/<scope>`, commits conventionnels (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `ci:`, `chore:`).
7. **Tests prioritaires du spec §23** : `test_health`, `test_create_incident`, `test_check_ip`, `test_check_vlan`, `test_check_dhcp`, `test_diagnosis`, `test_report_generation`. Ils doivent exister et passer.
8. **Commits propres** : stager explicitement, ne jamais committer `.env`, `*.db`, `node_modules`, `.venv`.
9. **Garder des messages de commit utiles** pour permettre un retour arrière (`git revert`) si besoin.
10. **Documenter au fur et à mesure** : mettre à jour `docs/api.md`, `docs/architecture.md`, `docs/demo.md`.

---

## 2. Commandes de vérification (toujours les mêmes)

| Vérification | Commande |
|---|---|
| Tests backend | `cd backend && python -m pytest` |
| Lint backend | `cd backend && ruff check .` |
| Tests frontend | `cd frontend && npm test` |
| Lint frontend | `cd frontend && npm run lint` |
| Build frontend | `cd frontend && npm run build` |
| Backend en dev | `cd backend && python -m uvicorn app.main:app --reload` |
| Frontend en dev | `cd frontend && npm run dev` |
| Swagger | `http://127.0.0.1:8000/docs` |

Définitions de done communes :
- Backend : `pytest` vert **et** `ruff check .` silencieux.
- Frontend : `npm test` vert, `npm run lint` silencieux, `npm run build` OK.

---

## 3. État actuel du repo (ce qui est déjà fait)

- [x] Dépôt GitHub initialisé (`main`), branches `develop` à créer.
- [x] Frontend React 19 + TypeScript + Vite initialisé (`frontend/`).
- [x] Backend FastAPI initialisé : `app/main.py` (routes `/`, `/health`), `app/core/config.py` (lit `backend/.env`).
- [x] Health check (`GET /health`) et tests backend (`tests/test_health.py`).
- [x] Infra dev : `.gitignore`, `.editorconfig`, `Makefile`, `AGENTS.md`, CI GitHub Actions, vitest + tests App.
- [ ] **Reste à créer** : SQLAlchemy + SQLite, simulateur réseau, outils de diagnostic, gestion incidents/rapports, voice agent AssemblyAI, RAG, UI.

---

## 4. Vue d'ensemble

Les phases gardent la numérotation du README (pour correspondance), mais l'**ordre d'exécution suggéré** diffère volontairement : on construit le noyau métier (simulateur + incidents) avant la voix, afin que l'agent vocal ait de vrais outils à appeler.

| Ordre | Phase (README) | Dépend de | Livrable clé |
|---|---|---|---|
| 1 | Phase 1 — Foundation (reste : SQLite) | — | Base SQLAlchemy + modèle Incident |
| 2 | Phase 4 — Network Simulator | P1 | `simulator/devices.json`, outils de diagnostic |
| 3 | Phase 6 — Incident management | P1 | CRUD incidents + génération de rapport |
| 4 | Phase 3 — Agentic capabilities | P4, P6 | Définition des tools, tool calling |
| 5 | Phase 2 — Voice Agent | P3 | Token temporaire, WebSocket, STT/TTS |
| 6 | Phase 5 — Knowledge / RAG | P5 | Index FAISS + retriever |
| 7 | Phase 7 — UI | P5, P6 | Panneaux voix/transcript/diagnostic/incident |
| 8 | Phase 8 — Hackathon | Toutes | Démo bout en bout, pitch, soumission |

Graphe de dépendances résumé : `P1 → P4 → P6 → P3 → P2` ; `P4 (docs) → P5` ; `P5+P6 → P7` ; `tout → P8`.

---

## Phase 1 — Foundation (reste : SQLite)

Objectif : rendre le backend persistant et structuré.

- [ ] Ajouter les dépendances : `sqlalchemy` (+ `aiosqlite` si besoin asynchrone) dans `backend/requirements.txt`.
- [ ] Créer `backend/app/database.py` : moteur SQLite (`DATABASE_URL`, défaut `sqlite:///./voiceops.db`), `SessionLocal`, `Base`, init des tables au démarrage.
- [ ] Créer `backend/app/models/` :
  - [ ] `incident.py` — champs du spec §21 : `id, title, description, device, category, severity, diagnosis, root_cause, status, created_at, updated_at`.
  - [ ] `session.py` — `id, incident_id, started_at, ended_at`.
  - [ ] `report.py` — `id, incident_id, content, created_at`.
  - [ ] `tool_call.py` — `id, session_id, tool_name, arguments, result, created_at`.
- [ ] Initialiser les tables au démarrage (fonction `init_db()` appelée côté `app.main`).

**Validation** : `pytest` vert ; un test d'import des modèles + création de la base passe ; `backend/voiceops.db` créé et ignoré par Git.

---

## Phase 4 — Network Simulator

Objectif : un environnement réseau simulé, reproductible et démontrable.

- [ ] Créer les données simulées dans `simulator/` :
  - [ ] `devices.json` — équipements (PC, switch, router, serveurs DHCP/DNS) avec `ip`, `gateway`, `vlan`, `expected_vlan`, `dhcp`, `status`.
  - [ ] `topology.json` — liens/ports (ex. `PC-B204 → Gi0/12`).
  - [ ] `scenarios.json` — les 5 scénarios du spec §19 (VLAN, DHCP, DNS, Gateway, Interface down).
- [ ] Créer `backend/app/network/simulator.py` : chargement des JSON, état simulant le réseau (accès bloqué/réel interdit).
- [ ] Créer `backend/app/network/devices.py` : helpers (`get_device`, `list_devices`, `get_scenario`).
- [ ] Créer `backend/app/network/diagnostics.py` : les fonctions de diagnostic pures et testables :
  - [ ] `check_ip_configuration(device)`
  - [ ] `check_vlan(device)` — détecte `vlan != expected_vlan` (VLAN mismatch).
  - [ ] `check_dhcp(device)` — détecte APIPA `169.254.x.x` (DHCP failure).
  - [ ] `check_dns(host)`, `ping_host(host)`, `traceroute(host)`, `check_gateway(device)`, `get_device_status(device)`.
- [ ] Exposer un router API de diagnostic : `backend/app/api/routes/diagnostics.py` (monté sur `/api/diagnostics`).

**Validation** : tests `test_check_ip`, `test_check_vlan`, `test_check_dhcp`, `test_diagnosis` passent (ex. : `PC-B204` → DHCP failure + VLAN mismatch). Swagger : `/api/diagnostics/device/{name}` renvoie l'état simulé.

---

## Phase 6 — Incident management

Objectif : transformer un diagnostic en incident et générer un rapport.

- [ ] Créer `backend/app/api/routes/incidents.py` (monté sur `/api/incidents`) :
  - [ ] `POST /` — créer un incident (body Pydantic).
  - [ ] `GET /` — lister (avec filtre par statut).
  - [ ] `GET /{id}` — détail.
  - [ ] `PATCH /{id}` — mettre à jour (statuts : `OPEN`, `INVESTIGATING`, `RESOLVED`, `CLOSED`).
  - [ ] `GET /{id}/history` — historique des changements de statut.
- [ ] Créer `backend/app/api/routes/reports.py` (monté sur `/api/reports`) :
  - [ ] `POST /api/incidents/{id}/report` — génère le rapport structuré (format spec §4.6 : date, équipement, symptôme, diagnostic, cause probable, actions, statut).
- [ ] Modèle `report` alimenté en base (`reports` table).

**Validation** : tests `test_create_incident` et `test_report_generation` passent (création + génération + `incident.status` cohérent). Persistance vérifiée dans `backend/voiceops.db`.

---

## Phase 3 — Agentic capabilities

Objectif : l'agent décide et appelle des outils quand c'est nécessaire.

- [ ] Créer `backend/app/agents/tools.py` : enregistrement des outils = fonctions de la Phase 4/6 exposées avec nom, description, schéma JSON des arguments (`check_vlan`, `check_dhcp`, `ping_host`, `create_incident`, `generate_report`, …).
- [ ] Créer `backend/app/agents/prompts.py` : le prompt système — agent spécialisé réseaux, en français, utilise les outils uniquement si nécessaire (RAG seulement si info documentaire requise).
- [ ] Créer `backend/app/voice/events.py` : le **middleware de tool calling** — intercepte l'appel outil demandé par l'agent, exécute la fonction Python (blanc-liste), renvoie le résultat à l'agent.
- [ ] Gestion d'erreurs : outil inconnu → message explicite, jamais de shell arbitraire.
- [ ] Journaliser les appels dans la table `tool_calls`.

**Validation** : tests unitaires du mapping outil→fonction (argument invalide → erreur propre) ; vérifier manuellement dans Swagger un « dry run » du flow (`check_vlan → create_incident → generate_report`).

---

## Phase 2 — Voice Agent

Objectif : le scénario complet parle et répond à la voix.

- [ ] Créer `backend/app/core/security.py` : helpers (validation d'entrées, génération token temporaire).
- [ ] Créer `backend/app/voice/assemblyai.py` :
  - [ ] `GET /api/voice-token` → génère un *temporary token* côté serveur à partir de `ASSEMBLYAI_API_KEY` (jamais transmise au front).
  - [ ] Gestion des sessions voix (`backend/app/voice/sessions.py`) : `create`, `end`.
- [ ] Du côté navigateur, connecter le microphone au WebSocket AssemblyAI (voir docs officielles AssemblyAI *Voice Agent* au moment de l'implémentation — schéma exact à confirmer) :
  - [ ] Fetch du token ; ouverture du WebSocket.
  - [ ] Capture micro + AudioWorklet.
  - [ ] STT ↔ LLM ↔ TTS avec détection de tour + interruptions.
- [ ] Brancher le middleware d'outils (Phase 3) sur le flux de l'agent.

**Validation** : en local — 1 phrase parlée → réponse vocale de l'agent ; si l'utilisateur dit « le PC 204 n'a plus de réseau », l'agent pose une question et enchaîne sur les outils. Les tests automatisés restent limités (pas de micro en CI) : valider le contrat `GET /api/voice-token` par un test HTTP.

---

## Phase 5 — Knowledge / RAG

Objectif : réponse enrichie par la documentation réseau interne.

- [ ] Alimenter `knowledge/` : créer `cisco/`, `networking/`, `telecom/`, `troubleshooting/` avec quelques notes au format markdown (VLAN, DHCP, DNS, APIPA, check-list de base).
- [ ] Créer `backend/app/rag/embeddings.py` : génération d'embeddings (modèle local ou API selon dispo).
- [ ] Créer `backend/app/rag/index.py` : parsing + chunking des documents, index **FAISS** (`faiss-cpu`), sauvegarde côté backend.
- [ ] Créer `backend/app/rag/retriever.py` : recherche sémantique → contexte pertinent renvoyé à l'agent.
- [ ] Intégration : l'agent intercepte la recherche uniquement quand des connaissances documentaires sont nécessaires (pas pour chaque réponse).

**Validation** : script/test « indexer → interroger » retourne des chunks pertinents (ex. requête « adresse APIPA » → doc DHCP). Pas de blocage si aucun document : comportement dégradé propre.

---

## Phase 7 — UI

Objectif : une interface de démo claire (voice-first).

- [ ] `frontend/src/services/api.ts` : client HTTP vers `localhost:8000` (proxy Vite en dev si besoin : `/api` → `http://localhost:8000`).
- [ ] `frontend/src/hooks/useVoiceAgent.ts` : logique microphone/WebSocket.
- [ ] Composants (`frontend/src/components/`) :
  - [ ] `VoiceInterface.tsx` — bouton micro, états (écoute/parle).
  - [ ] `Transcript.tsx` — transcription temps réel.
  - [ ] `ToolCall.tsx` — notification des appels d'outils.
  - [ ] `DiagnosisPanel.tsx` — résultat du diagnostic (IP, DHCP, VLAN, cause).
  - [ ] `IncidentPanel.tsx` — incident créé + rapport.
- [ ] Pages (`frontend/src/pages/`) : `Dashboard.tsx`, `Incident.tsx`.
- [ ] Adapter `App.tsx` : routing simple + mise en page (Tailwind CSS si souhaité).

**Validation** : `npm test`, `npm run lint`, `npm run build` verts ; parcours UI : clic micro → phrase → transcript → appel outil → panneau diagnostic → incident visible. Les composants clés ont au moins un test (rendu + interaction simple).

---

## Phase 8 — Hackathon

Objectif : une démo impeccable et la soumission.

- [ ] Déploiement : héberger backend (ex. Render/Railway) + frontend (Vercel) ; masquer `ASSEMBLYAI_API_KEY` en variable d'environnement.
- [ ] Recette de démo complète : rejouer le scénario MVP de bout en bout 3 fois sans erreur.
- [ ] `docs/demo.md` : script de démo (phrases à dire, ordre, fallback si l'API est indisponible).
- [ ] Enregistrer la démo (vidéo courte, voix claire).
- [ ] Préparer le pitch (problème, solution, architecture, démo, stack).
- [ ] Préparer le README final (badges CI, captures, instructions).
- [ ] Soumission finale.

---

## 5. Estimation de charge (indicatif)

| Phase | Effort estimé |
|---|---|
| P1 (reste : SQLite) | ~2–3 h |
| P4 Simulator | ~3–4 h |
| P6 Incidents | ~3–4 h |
| P3 Agentic | ~3 h |
| P2 Voice Agent | ~6–8 h (le plus risqué) |
| P5 RAG | ~3–4 h |
| P7 UI | ~4–6 h |
| P8 Démo + pile | ~3–4 h |

Budget utile : ~28–36 h. **P2 (voix) est l'étape critique** → la démarrer tôt pour absorber les aléas de l'API.

---

## 6. Pièges à éviter

- **S'autoriser à remonter le temps** : règle non, travailler sur `feature/*` et committer souvent par petites unités vertes ; utiliser `git revert` plutôt que `git reset` une fois poussé.
- **Tester en fin de phase** : non. Chaque tâche = valider immédiatement (`pytest`/`npm test`).
- **Exposer la clé API** : le token navigateur est le SEUL mécanisme autorisé côté client.
- **Appeler de vraies commandes réseau** (`ping`, `traceroute`, SSH) depuis le backend : interdit dans le MVP.
- **FAISS sur Windows** : utiliser `pip install faiss-cpu` ; prévoir un fallback (index simple) si l'installation échoue.
- **Le linker front↔back** : vérifier le CORS/cors en dev (`localhost:5173 → localhost:8000`) dès la Phase 7.

---

## 7. Comment utiliser ce document avec un agent IA

Lors de chaque session, demander :
1. « Quelles étapes de `docs/ROADMAP_EXECUTION.md` sont en cours ? » (le document sert de mémoire partagée).
2. « Termine l'étape **[n]** puis coche la case et valide par les commandes §2 ».
3. « Fais un commit conventionnel de l'étape [n] si verte ».

L'agent doit cocher les cases au fil de l'eau et ne **jamais** sauter une validation.