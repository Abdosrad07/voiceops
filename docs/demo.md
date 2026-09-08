# VoiceOps — Démo & mise en route

## Prérequis

- Python 3.12, Node 18+.
- Clé AssemblyAI (Voice Agent API). Copier `backend/.env.example` vers
  `backend/.env` et renseigner `ASSEMBLYAI_API_KEY`.

## Installation

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt

# Frontend
cd frontend
npm install
```

## Lancement (2 terminaux)

```bash
cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload   # :8000
cd frontend && npm run dev                                            # :5173
```

Ouvrir http://localhost:5173 (le proxy Vite redirige `/api` vers `:8000`).

## Scénario de démo (bout en bout)

Le scénario MVP : *« Le PC du bureau 204 n'a plus de réseau »*.

1. Cliquer **Parler** (microphone ; Chrome de préférence, casque conseillé).
2. L'agent se présente et écoute.
3. Dire : « Le PC 204 n'a plus de réseau ».
4. L'agent pose les questions ciblées, puis enchaîne les outils :
   `check_ip_configuration` → `check_gateway` → `check_dhcp` → `check_vlan`
   → `check_dns`.
5. Constat sur **PC-B204** : adresse APIPA (`169.254.14.23`), échec DHCP,
   VLAN du port = 10 au lieu de 20 → cause racine : **mauvais VLAN**.
6. L'agent crée l'incident (`create_incident`) et génère le rapport
   (`generate_report`), annoncé à voix haute.
7. Vérifier dans l'interface : panneau *Incidents* (sévérité, statut,
   cause probable) et *Outils exécutés*.

### Variantes de panne

| Équipement  | Panne simulée                |
| ----------- | ---------------------------- |
| PC-B204     | VLAN mismatch + échec DHCP   |
| PC-B203     | Panne DNS                    |
| PC-B201     | Passerelle injoignable       |

## Tests & validation

```bash
cd backend  && .venv\Scripts\python -m pytest && .venv\Scripts\ruff.exe check .
cd frontend && npm run lint && npm test && npm run build
```

49 tests backend + 13 tests frontend. Le pipeline GitHub Actions exécute ces
vérifications à chaque push/PR.

## Sans clé AssemblyAI (mode données)

`GET /api/voice-token` retourne 503 et l'interface signale l'absence de micro ;
les diagnostics, incidents et rapports restent utilisables via l'API/interface.