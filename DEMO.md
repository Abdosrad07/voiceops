# VoiceOps — Guide de démonstration

Ce guide explique comment lancer VoiceOps, vérifier qu'il fonctionne et
réaliser la démonstration (live ou scriptée) pour le hackathon.

Documentation de référence : `docs/demo.md` (scénario de bout en bout),
`docs/api.md` (endpoints), `docs/architecture.md` (flux vocal).

---

## 1. Prérequis

- Python 3.12+, Node 18+.
- Une clé AssemblyAI (Voice Agent API) dans `backend/.env` :

```bash
cd backend
copy .env.example .env   # PowerShell
# .env : ASSEMBLYAI_API_KEY=votre_cle
```

Sans clé, tout fonctionne sauf la voix (l'interface signale l'absence de
micro ; `/api/voice-token` répond 503).

## 2. Démarrage rapide

```bash
# 1) Dépendances (Windows)
cd backend && .venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
cd frontend && npm install

# 2) Backend — http://localhost:8000
cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload

# 3) Frontend — http://localhost:5173 (autre terminal)
cd frontend && npm run dev
```

## 3. Vérification rapide (30 secondes)

```powershell
# Backend démarré et en bonne santé
Invoke-RestMethod http://localhost:8000/health                    # status: ok
Invoke-RestMethod http://localhost:8000/health/deep               # checks db/rag/asr

# Créer un incident + générer le rapport
$body = @{ title = "PC-B204 sans réseau"; description = "Le PC du bureau 204 n'accède plus au réseau.";
           device = "PC-B204"; category = "Network / VLAN"; severity = "medium";
           diagnosis = "VLAN incorrect"; root_cause = "Port sur VLAN 10 au lieu de 20" } | ConvertTo-Json
$inc = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/incidents `
          -ContentType "application/json" -Body $body
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/incidents/$($inc.id)/report"

# Outil de diagnostic
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/tools/execute `
   -ContentType "application/json" -Body (@{ name = "check_vlan"; call_id = "c1";
   arguments = @{ device = "PC-B204" } } | ConvertTo-Json)
```

Frontend : ouvrir http://localhost:5173 — l'incident ci-dessus doit
apparaître dans le panneau *Incidents*.

## 4. Démo live (avec clé + micro)

La démo star : **« Le PC du bureau 204 n'a plus de réseau »**.

1. Cliquer **Parler** (Chrome, casque conseillé).
2. Dire : « Le PC 204 n'a plus de réseau ».
3. L'agent pose des questions ciblées puis enchaîne :
   `check_ip_configuration` → `check_gateway` → `check_dhcp` →
   `check_vlan` → `check_dns`.
4. Il conclut (adresse APIPA, DHCP KO, mauvais VLAN), crée l'incident
   (`create_incident`) et génère le rapport (`generate_report`).
5. Vérifier à l'écran : panneau *Incidents* (sévérité, statut, cause)
   et *Outils exécutés*.

Raccourci clavier : **Espace** pour démarrer/arrêter l'enregistrement.

## 5. Démo scriptée / repli sans micro

Même sans WebSocket (pas de clé, problème de réseau, salle bruyante),
la démo reste complète :

1. Lancer le backend et le frontend (section 2).
2. Exécuter les commandes de la section 3 — elles replay l'essentiel du
   scénario (diagnostic → incident → rapport) côté serveur.
3. Afficher dans *Incidents* l'incident créé, son statut et le rapport.
4. Narrer le flux vocal comme sur la capture 4.1 ci-dessous.

```
Technicien : « Le PC 204 n'a plus de réseau. »
VoiceOps   : notion de diagnostic → check_ip_configuration → APIPA détectée
             → check_dhcp → échec → check_vlan → mismatch (10 vs 20)
             → cause probable → create_incident → generate_report
Dashboard  : incident OPEN « VLAN incorrect », rapport #VO-xxx généré
```

## 6. Risques & contournements à connaître

| Risque | Contournement |
| --- | --- |
| Pas de clé AssemblyAI | Démo scriptée (section 3/5) ; `/health/deep` affiche `asr: down` (attendu). |
| Micro refusé / audio capté | Naviguer sans microphone ; le workflow API reste démontrable. |
| Barge-in parasite | Relancer l'écoute avec Espace ou le bouton. |
| Ports occupés | Changer le port du frontend (`npm run dev -- --port 5174`). |
| Latence réseau voix | Câble/meilleur réseau ; `ASSEMBLYAI_TIMEOUT_SECONDS` ajustable. |

## 7. Checklist avant présentation

- [ ] `make test` passe (76 backend + 19 frontend) — ou commandes d'AGENTS.md.
- [ ] http://localhost:8000/health → `200 ok`.
- [ ] http://localhost:5173 → interface VoiceOps servie.
- [ ] Micro + haut-parleurs testés (démo live).
- [ ] Un incident + un rapport créés à l'avance (démo scriptée prête).
- [ ] Le scénario complet rejoué une fois de bout en bout.