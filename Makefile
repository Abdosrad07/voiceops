.PHONY: install test lint build dev run

install: backend-install frontend-install   ## Install all dependencies

backend-install:                           ## Install backend deps
	cd backend && python -m pip install -r requirements.txt -r requirements-dev.txt

frontend-install:                          ## Install frontend deps
	cd frontend && npm install

test: backend-test frontend-test           ## Run all tests
backend-test:
	cd backend && python -m pytest
frontend-test:
	cd frontend && npm test

lint: backend-lint frontend-lint           ## Lint everything
backend-lint:
	cd backend && ruff check .
frontend-lint:
	cd frontend && npm run lint

build:                                     ## Build frontend
	cd frontend && npm run build

dev:                                       ## Start both dev servers (backend + frontend)
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd frontend && npm run dev

run:                                       ## Run backend only
	cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000