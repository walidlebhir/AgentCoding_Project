# CLI Agent — Fonctionnement & API FastAPI

## 1. Comment l'agent CLI fonctionne

L'agent CLI (`cli_agent/`) est un client Python en ligne de commande qui sert d'interface utilisateur au backend **FastAPI** (`src/Server.py`). Il suit une architecture **client-serveur** simple :

```
Terminal (CLI Agent) --HTTP--> FastAPI Backend --LLM--> Provider (Gemini/Groq)
```

### Flux d'exécution

1. **Saisie utilisateur** — L'utilisateur tape une commande (generate, edit, add, health) dans le terminal.
2. **Parsing** — `main.py` analyse la commande via Typer (mode direct) ou un REPL interactif.
3. **Client HTTP** — `core/client.py` envoie une requête HTTP au backend FastAPI via `httpx`.
4. **Génération LLM** — Le backend (`src/System_Agentic/`) sélectionne le meilleur provider disponible (Gemini/Groq), appelle le LLM, parse les fichiers générés, et les écrit sur disque.
5. **Réponse** — Le CLI reçoit le résultat JSON et télécharge/extrait le projet ZIP.

### Structure du CLI

| Fichier | Rôle |
|---------|------|
| `main.py` | Point d'entrée, REPL interactif, dispatch des commandes |
| `core/client.py` | Client HTTP avec retry (3 tentatives) |
| `core/parser.py` | Extraction du chemin `--path` et nettoyage du prompt |
| `commands/generate.py` | Logique de génération + téléchargement ZIP |
| `commands/edit.py` | Modification d'un projet existant |
| `commands/add.py` | Ajout d'une fonctionnalité |
| `utils/config.py` | Configuration (URL API, timeout) |
| `utils/logger.py` | Logs colorés dans le terminal |

---

## 2. API FastAPI — Endpoints REST

Le backend écoute sur `http://localhost:8000` (configurable via `SPRINGFORGE_API_URL`).

### `POST /generate` — Générer un projet

```json
// Requête
POST /generate
Content-Type: application/json

{
  "prompt": "create a user management api with crud"
}

// Réponse succès
{
  "success": true,
  "project_id": "proj_1717000000_a1b2c3",
  "download_url": "http://localhost:8000/download/proj_1717000000_a1b2c3",
  "filename": "proj_1717000000_a1b2c3.zip",
  "request_id": "a1b2c3d4",
  "duration_seconds": 12.5,
  "llm_calls": 1,
  "files_generated": 12,
  "provider": "gemini/gemini-2.5-flash",
  "cached": false
}
```

### `GET /health` — État des providers

```json
GET /health

{
  "status": "running",
  "version": "3.0.0",
  "providers": {
    "gemini/gemini-2.5-flash": {
      "state": "AVAILABLE",
      "calls": 5,
      "daily": 5,
      "remaining_daily": 1495,
      "remaining_minute": 3,
      "cooldown_remaining": 0
    }
  },
  "call_stats": {
    "global_calls": 12,
    "request_calls": 1
  }
}
```

### `GET /projects` — Liste des projets générés

```json
GET /projects

{
  "projects": ["proj_1717000000_a1b2c3", "proj_1716900000_d4e5f6"]
}
```

### `GET /download/{project_id}` — Télécharger un ZIP

```
GET /download/proj_1717000000_a1b2c3
→ application/zip
```

### `GET /` — Informations générales

```json
GET /

{
  "message": "SpringBoot Generator API",
  "version": "3.0.0",
  "global_llm_calls": 12,
  "providers": { ... },
  "endpoints": { ... }
}
```

### `GET /admin/reset` — Réinitialiser cache et compteurs

```json
GET /admin/reset

{
  "message": "Reset OK (3 cache entries cleared)"
}
```

---

## 3. Exemples de communication avec l'API

### Via curl

```bash
# Générer un projet
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"blog api with posts and comments"}'

# Vérifier la santé
curl http://localhost:8000/health

# Lister les projets
curl http://localhost:8000/projects

# Télécharger un projet
curl -o project.zip http://localhost:8000/download/proj_1717000000_a1b2c3
```

### Via le CLI (SpringForge)

```powershell
# Mode direct
python cli_agent\main.py generate "blog api"
python cli_agent\main.py health

# Mode interactif (REPL)
python cli_agent\main.py
> generate create a rest api
> health
> /exit
```

---

## 4. Gestion des providers (côté backend)

Le backend utilise un **rate limiter** avec machine à états :

```
AVAILABLE ──► RATE_LIMITED (cooldown < 60s)
          └─► QUOTA_EXCEEDED (cooldown 24h)
```

Ordre de priorité des providers :

| Priorité | Provider | RPM | TPD |
|----------|----------|-----|-----|
| 1 | `gemini/gemini-2.5-flash` | 5 | 1500 |
| 2 | `gemini/gemini-3-flash-preview` | 30 | 1500 |
| 3 | `gemini/gemini-2.5-flash-lite` | 10 | 20 |
| 4 | `groq/llama-3.3-70b-versatile` | 30 | 100k |
| 5 | `groq/mixtral-8x7b-32768` | 30 | 100k |

Si un provider est rate-limité ou a dépassé son quota, le suivant dans l'ordre est automatiquement utilisé (fallback).
