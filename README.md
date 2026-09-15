VoiceOps

«Your network. Your voice. Your copilot.»

VoiceOps est un assistant vocal intelligent spécialisé dans le diagnostic des incidents réseau.

Il permet à un technicien de décrire oralement un problème réseau, puis d'interagir avec un agent vocal capable de poser des questions, consulter une base de connaissances, exécuter des outils de diagnostic simulés et produire un rapport d'incident structuré.

Le projet est développé dans le cadre du AssemblyAI – Voice Agent Hackathon 2026.

---

1. Présentation

Le diagnostic réseau repose encore largement sur :

- des interfaces complexes ;
- des commandes CLI ;
- des documentations techniques dispersées ;
- l'expérience individuelle du technicien ;
- des procédures manuelles ;
- la rédaction manuelle des rapports d'incident.

VoiceOps propose une approche voice-first.

Au lieu de chercher manuellement les commandes et procédures, le technicien peut simplement dire :

«« Le PC du bureau 204 n'arrive plus à accéder au réseau. »»

VoiceOps peut alors :

1. comprendre le problème ;
2. poser des questions ciblées ;
3. analyser les informations fournies ;
4. appeler des outils de diagnostic ;
5. consulter la documentation technique ;
6. identifier une cause probable ;
7. proposer des actions correctives ;
8. générer un rapport d'incident.

---

2. Objectifs

Objectif principal

Construire un copilote vocal spécialisé pour les techniciens réseau.

Objectifs secondaires

- démontrer les capacités de la Voice Agent API d'AssemblyAI ;
- permettre une interaction vocale naturelle ;
- exploiter le tool calling ;
- intégrer une base de connaissances réseau ;
- simuler des diagnostics réseau ;
- réduire le temps nécessaire au diagnostic ;
- standardiser les procédures de troubleshooting ;
- générer automatiquement des rapports d'incident.

---

3. Démonstration cible

Le scénario principal du prototype est un incident réseau.

Exemple

Le technicien dit :

«« VoiceOps, le PC du bureau 204 n'a plus accès au réseau. »»

L'agent peut répondre :

«« D'accord. Est-ce que la connexion Ethernet est active ? »»

Le technicien :

«« Oui. »»

L'agent :

«« Quelle adresse IPv4 possède le poste ? »»

Le technicien :

«« 169.254.14.23. »»

VoiceOps peut alors appeler :

check_ip_configuration()
check_dhcp()
check_vlan()
check_gateway()

Le système identifie par exemple :

Adresse IP : 169.254.14.23
DHCP : Échec
VLAN actuel : 10
VLAN attendu : 20
Passerelle : Accessible

Puis l'agent explique :

«« Le poste possède une adresse APIPA et son port semble associé au mauvais VLAN. La cause probable est une configuration VLAN incorrecte. »»

Enfin, VoiceOps peut générer :

INCIDENT #VO-001

Catégorie :
Network / VLAN

Équipement :
PC-B204

Diagnostic :
VLAN incorrect

Cause probable :
Le port du poste est associé au VLAN 10
au lieu du VLAN 20.

Sévérité :
Medium

Actions recommandées :
1. Vérifier le port Gi0/12.
2. Vérifier son VLAN.
3. Corriger l'affectation du port.
4. Renouveler la configuration DHCP.

---

4. Fonctionnalités

4.1 Voice Agent

Le cœur de VoiceOps repose sur la AssemblyAI Voice Agent API.

Fonctions :

- capture microphone ;
- speech-to-text ;
- compréhension du langage naturel ;
- réponse vocale ;
- détection des tours de parole ;
- interruptions ;
- tool calling ;
- conversation temps réel.

---

4.2 Diagnostic réseau

VoiceOps possède des outils spécialisés permettant à l'agent d'obtenir des informations sur l'environnement réseau simulé.

Exemples :

check_ip_configuration()
check_gateway()
check_dhcp()
check_dns()
check_vlan()
ping_host()
traceroute()
get_device_status()

Les outils sont appelés par l'agent uniquement lorsque cela est nécessaire.

---

4.3 Network Simulator

Le projet utilise un environnement réseau simulé afin de rendre les scénarios :

- reproductibles ;
- sûrs ;
- faciles à tester ;
- faciles à démontrer.

Le simulateur peut représenter :

Router
Switch
PC
DHCP Server
DNS Server
VLAN
Gateway

Il peut également représenter des incidents prédéfinis :

DHCP failure
VLAN mismatch
DNS failure
Gateway unreachable
Wrong IP configuration
Interface down

---

4.4 Knowledge Base / RAG

VoiceOps peut consulter une base documentaire spécialisée.

Domaines prévus :

Cisco
VLAN
DHCP
DNS
ARP
TCP/IP
OSPF
STP
Linux networking
Network troubleshooting
Telecommunications

Le système utilise la recherche sémantique pour fournir à l'agent les informations pertinentes avant sa réponse.

---

4.5 Gestion des incidents

Chaque diagnostic peut être transformé en incident.

Un incident contient notamment :

ID
Date
Équipement
Symptômes
Diagnostic
Cause probable
Sévérité
Actions recommandées
Statut
Conversation associée

Statuts possibles :

OPEN
INVESTIGATING
RESOLVED
CLOSED

---

4.6 Génération de rapports

Après un diagnostic, VoiceOps peut générer automatiquement un compte rendu structuré.

Exemple :

Incident #VO-001

Date :
2026-09-XX

Équipement :
PC-B204

Symptôme :
Absence de connectivité réseau.

Diagnostic :
Échec DHCP associé à un mauvais VLAN.

Cause probable :
Configuration incorrecte du port du switch.

Actions recommandées :
...

Statut :
OPEN

---

5. Architecture

USER
│
│ 🎙️
▼
┌──────────────────┐
│ React │
│ TypeScript │
│ │
│ Voice Interface │
│ Transcript │
│ Diagnosis │
│ Incident Panel │
└────────┬─────────┘
│
│ HTTPS
▼
┌──────────────────┐
│ FastAPI │
│ Python │
│ │
│ REST API │
│ Auth / Sessions │
│ Token generation │
│ Business logic │
└────────┬─────────┘
│
│ Temporary Token
▼
┌──────────────────┐
│ AssemblyAI │
│ Voice Agent API │
│ │
│ STT │
│ LLM │
│ TTS │
│ Turn Detection │
│ Tool Calling │
└────────┬─────────┘
│
Tool Calls
│
▼
┌──────────────────┐
│ FastAPI Tools │
└────────┬─────────┘
│
┌───────────┴───────────┐
▼ ▼
┌──────────────┐ ┌──────────────┐
│ Network │ │ Knowledge │
│ Simulator │ │ Base │
│ │ │ │
│ Devices │ │ Documents │
│ VLANs │ │ RAG / TF-IDF │
│ DHCP │ │ │
│ DNS │ │ │
└──────────────┘ └──────────────┘
│ │
└───────────┬───────────┘
▼
┌────────────┐
│ SQLite │
│ │
│ Incidents │
│ Sessions │
│ Reports │
└────────────┘

---

6. Stack technique

Frontend

React
TypeScript
Vite
CSS (vanilla, aucun framework UI)

Backend

Python 3.12+
FastAPI
Uvicorn
Pydantic
SQLAlchemy (sync)

Voice

AssemblyAI Voice Agent API
WebSocket
AudioWorklet

IA / Knowledge

AssemblyAI Voice Agent
RAG local (index TF-IDF + recherche sémantique)
Retrieval paresseux (dégradé propre sans index)

Database

SQLite

SQLite est volontairement utilisé pour le MVP afin de réduire la complexité opérationnelle.

Aucun serveur PostgreSQL n'est nécessaire pour le développement ou la démonstration initiale.

Versioning

Git
GitHub

---

7. Pourquoi SQLite ?

Le projet est avant tout un prototype de hackathon.

SQLite permet :

- zéro serveur de base de données ;
- configuration minimale ;
- installation simple ;
- développement local rapide ;
- sauvegarde facile ;
- intégration simple avec SQLAlchemy.

La base sera stockée localement :

backend/voiceops.db

Elle est suffisante pour le MVP.

Une migration vers PostgreSQL pourra être envisagée ultérieurement si VoiceOps devient un véritable produit multi-utilisateur.

---

8. Structure du projet

voiceops/
│
├── frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── MicButton.tsx
│   │   │   ├── TranscriptPanel.tsx
│   │   │   ├── ToolCallList.tsx
│   │   │   ├── IncidentPanel.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── RecordBar.tsx
│   │   │
│   │   ├── hooks/
│   │   │   └── useVoiceAgent.ts
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── voiceProtocol.ts
│   │   │
│   │   ├── utils/
│   │   │   └── useDebounce.ts
│   │   │
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── public/
│   │   └── pcm-worklet.js
│   ├── package.json
│   ├── vitest.config.ts
│   └── vite.config.ts
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       ├── voice.py
│   │   │       ├── incidents.py
│   │   │       ├── diagnostics.py
│   │   │       ├── networks.py
│   │   │       └── reports.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   ├── middleware.py
│   │   │   └── resilience.py
│   │   │
│   │   ├── voice/
│   │   │   ├── assemblyai.py
│   │   │   ├── sessions.py
│   │   │   └── events.py
│   │   │
│   │   ├── agents/
│   │   │   ├── prompts.py
│   │   │   └── tools.py
│   │   │
│   │   ├── network/
│   │   │   ├── active.py
│   │   │   ├── imports.py
│   │   │   ├── simulator.py
│   │   │   ├── devices.py
│   │   │   └── diagnostics.py
│   │   │
│   │   ├── rag/
│   │   │   ├── embeddings.py
│   │   │   ├── index.py
│   │   │   └── retriever.py
│   │   │
│   │   ├── models/
│   │   │   ├── incident.py
│   │   │   ├── network.py
│   │   │   ├── session.py
│   │   │   ├── report.py
│   │   │   └── tool_call.py
│   │   │
│   │   └── database.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env
│
├── knowledge/
│   ├── cisco/
│   ├── networking/
│   ├── telecom/
│   └── troubleshooting/
│
├── simulator/
│   ├── devices.json
│   ├── topology.json
│   └── scenarios.json
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── demo.md
│   └── ROADMAP_EXECUTION.md
│
├── Makefile
├── .gitignore
├── .env.example
├── DEMO.md
└── README.md

---

9. Environnement de développement

Le projet est développé initialement sous Windows.

Logiciels nécessaires

Windows 10/11
Git
VS Code
Python 3.12+
Node.js 22 LTS
npm
Google Chrome

Docker, WSL, PostgreSQL et Redis ne sont pas requis pour le MVP.

---

10. Installation

10.1 Cloner le dépôt

git clone <repository-url>
cd voiceops

---

11. Backend

Entrer dans le backend :

cd backend

Créer l'environnement virtuel :

py -3.12 -m venv .venv

Activer l'environnement :

.\.venv\Scripts\Activate.ps1

Installer les dépendances :

pip install -r requirements.txt

---

12. Variables d'environnement

Créer :

backend/.env

à partir de :

.env.example

Exemple :

ASSEMBLYAI_API_KEY=your_assemblyai_api_key

DATABASE_URL=sqlite:///./voiceops.db

ENVIRONMENT=development

Important

Le fichier ".env" ne doit jamais être envoyé sur GitHub.

Il est présent dans ".gitignore".

---

13. Lancer le backend

Depuis :

backend/

lancer :

uvicorn app.main:app --reload

API :

http://127.0.0.1:8000

Documentation Swagger :

http://127.0.0.1:8000/docs

Health check :

http://127.0.0.1:8000/health

---

14. Frontend

Dans un deuxième terminal :

cd frontend

Installer les dépendances :

npm install

Lancer le serveur :

npm run dev

Application :

http://localhost:5173

---

15. Communication frontend/backend

En développement :

React
localhost:5173
│
│ HTTP
▼
FastAPI
localhost:8000

Pour la voix :

React
│
│ GET /api/voice-token
▼
FastAPI
│
│ AssemblyAI API Key
▼
AssemblyAI
│
│ Temporary Token
▼
FastAPI
│
▼
React
│
│ WebSocket
▼
AssemblyAI Voice Agent

La clé API AssemblyAI reste exclusivement côté serveur.

---

16. Flux vocal

1. User clicks microphone
↓
2. Browser requests temporary token
↓
3. FastAPI generates AssemblyAI token
↓
4. Browser opens WebSocket
↓
5. Microphone captures audio
↓
6. Audio is sent to AssemblyAI
↓
7. AssemblyAI transcribes speech
↓
8. Agent understands request
↓
9. Agent decides whether a tool is required
↓
10. Tool is executed
↓
11. Result returned to agent
↓
12. Agent generates response
↓
13. Response converted to audio
↓
14. Browser plays response

---

17. Tool Calling

VoiceOps définit des outils spécialisés.

Exemple :

check_ip_configuration(device)

check_vlan(device)

check_dhcp(device)

check_gateway(device)

ping_host(host)

check_dns(host)

create_incident(data)

generate_report(incident_id)

Le LLM décide quand utiliser ces outils.

---

18. Network Simulator

Le simulateur fournit un environnement réseau contrôlé.

Exemple :

{
"PC-B204": {
"ip": "169.254.14.23",
"gateway": "192.168.20.1",
"vlan": 10,
"expected_vlan": 20,
"dhcp": "failed",
"status": "online"
}
}

Le système peut alors détecter :

DHCP failure
+
VLAN mismatch

sans toucher à un équipement réseau réel.

---

19. Scénarios de démonstration

Le MVP doit comporter plusieurs scénarios prédéfinis.

Scénario 1 — VLAN

Symptôme :
PC inaccessible

Cause :
Mauvais VLAN

Scénario 2 — DHCP

Symptôme :
Adresse 169.254.x.x

Cause :
Échec DHCP

Scénario 3 — DNS

Symptôme :
Internet accessible par IP
mais pas par nom

Cause :
Problème DNS

Scénario 4 — Gateway

Symptôme :
PC correctement configuré
mais passerelle inaccessible

Cause :
Problème de connectivité locale

Scénario 5 — Interface

Symptôme :
Équipement inaccessible

Cause :
Interface désactivée

---

20. RAG

Les documents de connaissance sont stockés dans :

knowledge/

Organisation :

knowledge/
├── cisco/
├── networking/
├── telecom/
└── troubleshooting/

Pipeline :

Documents
↓
Parsing
↓
Chunking
↓
Vectorisation TF-IDF
↓
Index TF-IDF local
↓
Semantic Search
↓
Relevant Context
↓
Voice Agent

Le RAG doit être utilisé uniquement lorsque les informations documentaires sont nécessaires.

---

21. Base de données SQLite

La base contient notamment :

"incidents"

id
title
description
device
category
severity
diagnosis
root_cause
status
created_at
updated_at

"sessions"

id
incident_id
started_at
ended_at

"reports"

id
incident_id
content
created_at

"tool_calls"

id
session_id
tool_name
arguments
result
created_at

---

22. Sécurité

Principes :

- clé AssemblyAI uniquement côté backend ;
- ".env" ignoré par Git ;
- temporary tokens pour le navigateur ;
- validation des entrées ;
- aucun accès direct à des équipements réels dans le MVP ;
- outils réseau simulés ;
- aucune commande système arbitraire exécutée par le LLM.

Le modèle ne doit jamais pouvoir exécuter directement :

cmd.exe
PowerShell
bash
Cisco CLI

sans mécanisme de contrôle explicite.

---

23. Tests

Les tests doivent couvrir :

Backend
├── API
├── database
├── diagnostic tools
├── simulator
├── RAG
└── incident management

Tests prioritaires :

test_health()
test_create_incident()
test_check_ip()
test_check_vlan()
test_check_dhcp()
test_diagnosis()
test_report_generation()

---

24. Git workflow

Branches principales :

main
develop

Branches fonctionnelles :

feature/frontend
feature/voice-agent
feature/network-simulator
feature/rag
feature/incidents
feature/reports

Convention de commit :

feat: add voice agent connection
feat: add network simulator
feat: add vlan diagnostic tool
fix: handle websocket disconnect
docs: update setup instructions
refactor: simplify diagnostic service
test: add vlan diagnostic tests

---

25. Roadmap

Statut au 14/09/2026 : Phases 1 à 7 réalisées, Phase 8 en cours (reste :
démo enregistrée, pitch).

Phase 1 — Foundation

- [x] Initialiser GitHub
- [x] Initialiser React
- [x] Initialiser FastAPI
- [x] Configurer SQLite
- [x] Configurer ".env"
- [x] Health check

Phase 2 — Voice Agent

- [x] Temporary token
- [x] WebSocket AssemblyAI
- [x] Microphone
- [x] AudioWorklet
- [x] Speech-to-text
- [x] Agent response
- [x] Text-to-speech
- [x] Interruptions

Phase 3 — Agentic capabilities

- [x] Tool definitions
- [x] Tool calling
- [x] Tool results
- [x] Agent reasoning
- [x] Error handling

Phase 4 — Network Simulator

- [x] Devices
- [x] Topology
- [x] VLAN
- [x] DHCP
- [x] DNS
- [x] Gateway
- [x] Diagnostic scenarios

Phase 5 — Knowledge

- [x] Documents
- [x] Chunking
- [x] Vectorisation TF-IDF
- [x] Index TF-IDF local
- [x] Retrieval
- [x] Agent integration

Phase 6 — Incident management

- [x] Create incident
- [x] Update incident
- [x] Incident history
- [x] Diagnosis
- [x] Report generation

Phase 7 — UI

- [x] Voice interface
- [x] Transcript
- [x] Agent status
- [x] Tool calls
- [x] Diagnosis panel
- [x] Incident panel
- [x] History

Phase 8 — Hackathon

- [ ] Deploy application
- [x] Test complete scenario
- [ ] Record demo
- [ ] Prepare pitch
- [x] Prepare README
- [ ] Final submission

---

26. MVP Definition

Le MVP est considéré comme terminé lorsque le scénario suivant fonctionne de bout en bout :

Technician
│
│ "The PC has no network"
▼
VoiceOps
│
├── asks questions
│
├── gets IP
│
├── checks DHCP
│
├── checks VLAN
│
├── identifies cause
│
└── explains diagnosis
│
▼
Incident Report

Le MVP ne nécessite pas :

❌ Cisco hardware
❌ SNMP
❌ Kubernetes
❌ PostgreSQL
❌ Redis
❌ LiveKit
❌ multi-agent architecture
❌ mobile application
❌ complex authentication

---

27. Principes de développement

Simplicité avant sophistication

Le projet est un hackathon.

Toute fonctionnalité doit être évaluée selon :

Valeur pour la démo
/
Complexité ajoutée

Voice-first

La voix doit rester le centre de l'expérience.

Agentique

VoiceOps doit utiliser ses outils pour agir et diagnostiquer, pas uniquement générer du texte.

Spécialisation

L'agent est spécialisé dans les réseaux.

Sécurité

Aucun accès arbitraire à des systèmes réels.

Démontrabilité

Chaque fonctionnalité importante doit pouvoir être montrée facilement pendant la présentation.

---

28. Future Evolution

Après le hackathon, VoiceOps pourrait évoluer vers :

VoiceOps
│
├── Network Troubleshooting
├── Cisco Assistant
├── Linux Network Assistant
├── NOC Copilot
├── Telecom Assistant
├── FTTH Troubleshooting
├── IT Helpdesk
└── Incident Management

Des intégrations réelles pourraient ensuite être ajoutées :

SNMP
Syslog
NetBox
Cisco APIs
SSH
Monitoring systems
Ticketing systems

Ces fonctionnalités ne font pas partie du MVP du hackathon.

---

29. Licence

À définir avant la publication finale.

---

30. Statut du projet

Status: MVP fonctionnel (démo prête)
Version: 0.1.0
Environment: Windows
Database: SQLite
Target: AssemblyAI Voice Agent Hackathon 2026

---

31. Vision

«VoiceOps transforms network troubleshooting from a command-driven workflow into a natural conversation.»

Le technicien n'a plus besoin de mémoriser chaque commande ou de parcourir plusieurs documents avant de commencer son diagnostic.

Il décrit le problème.

VoiceOps écoute, questionne, analyse, utilise ses outils et explique la solution.

---

32. Démarrage rapide

Prérequis : Python 3.12, Node 18+, clé AssemblyAI (`backend/.env`, voir
`backend/.env.example`).

```bash
cd backend && python -m pip install -r requirements.txt -r requirements-dev.txt
cd frontend && npm install
```

Lancement : backend `python -m uvicorn app.main:app --reload` (port 8000),
frontend `npm run dev` (port 5173). Documentation :

- `DEMO.md` — guide de démonstration (live et scriptée) et vérification rapide.
- `docs/api.md` — référence des endpoints.
- `docs/architecture.md` — architecture et flux vocal.
- `docs/demo.md` — scénario de démo de bout en bout.
- `docs/ROADMAP_EXECUTION.md` — plan d'exécution par phases.

Validation locale : `make test` (ou les commandes du tableau d'AGENTS.md).
Le pipeline GitHub Actions exécute lint + tests + build à chaque push/PR.
