# voiceops — Agent audio pour le troubleshooting en télécoms

## Stack
- `backend/` — Python 3.12 + FastAPI (+ WebSockets, Pydantic, Uvicorn)
- `frontend/` — React 19 + TypeScript + Vite + Vitest
- CI/CD — GitHub Actions (`.github/workflows/ci.yml`)

## Installation

Backend (recommendé : venv), puis :

```bash
cd backend
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Frontend :

```bash
cd frontend
npm install
```

## Commandes utiles

| Action                      | Commande                                                  |
| --------------------------- | --------------------------------------------------------- |
| Lancer le backend (dev)     | `cd backend && python -m uvicorn app.main:app --reload`    |
| Lancer le frontend (dev)    | `cd frontend && npm run dev`                              |
| Lint backend                | `cd backend && ruff check .`                              |
| Tests backend               | `cd backend && python -m pytest`                          |
| Lint frontend               | `cd frontend && npm run lint`                             |
| Tests frontend              | `cd frontend && npm test`                                 |
| Build frontend              | `cd frontend && npm run build`                            |
| Tout installer / tester     | `make install` / `make test`                              |

## Configuration

Copier `backend/.env.example` vers `backend/.env` et ajuster si besoin.
Le backend écoute par défaut sur `http://localhost:8000` (docs Swagger sur `/docs`).

## CI

Le pipeline CI (`.github/workflows/ci.yml`) s'exécute sur chaque push vers `main`
et chaque PR : lint + tests backend (pytest/ruff), lint + tests + build frontend
(eslint/vitest/vite).