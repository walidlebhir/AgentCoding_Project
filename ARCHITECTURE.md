# SpringBoot Agentic Generator — Architecture

## Vue d'ensemble

Générateur d'applications Spring Boot via un unique appel LLM. Architecture **stateless**, **mono-call**, avec fallback multi-provider et cache intégré.

```
┌─────────────────────────────────────────────────────────┐
│                    Client HTTP                           │
│  POST /generate  GET /download/{id}  GET /health        │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    Server.py (FastAPI)                    │
│  - Routage                                            │
│  - Génération d'ID de requête (request_id)             │
│  - Compression ZIP du projet                           │
│  - Réponse JSON structurée                             │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              single_generator.py                         │
│  - Cache SHA256 (TTL 2h)                               │
│  - Boucle de retry (max 3 tentatives)                  │
│  - Parsing du format <<<FILE:path>>>...<<<END_FILE>>>   │
│  - Écriture des fichiers sur disque                    │
│  - Délégation du choix du provider à rate_limiter      │
└──────┬──────────────────────────────┬───────────────────┘
       │                              │
       ▼                              ▼
┌──────────────┐           ┌────────────────────┐
│   config.py   │           │  rate_limiter.py    │
│  create_llm() │◄─────────│  ProviderManager    │
│  has_key()    │           │  ProviderState      │
└──────┬───────┘           │  (AVAILABLE,         │
       │                   │   RATE_LIMITED,      │
       ▼                   │   QUOTA_EXCEEDED)    │
┌──────────────┐           └────────────────────┘
│  CrewAI LLM  │
│  Gemini      │
│  Groq        │
└──────────────┘
```

## Flux de génération

```
Client                     Server              single_generator          ProviderManager          LLM
  │                          │                       │                       │                    │
  │  POST /generate          │                       │                       │                    │
  │────────────────────────►│                       │                       │                    │
  │                          │  generate_project()   │                       │                    │
  │                          │─────────────────────►│                       │                    │
  │                          │                       │  get_best()          │                    │
  │                          │                       │─────────────────────►│                    │
  │                          │                       │◄─────────────────────│                    │
  │                          │                       │     model_name       │                    │
  │                          │                       │                       │                    │
  │                          │                       │  create_llm(model)   │                    │
  │                          │                       │──────────────────────────────────────────►│
  │                          │                       │                       │                    │
  │                          │                       │     llm.call(prompt)  │                    │
  │                          │                       │──────────────────────────────────────────►│
  │                          │                       │                       │                    │
  │                          │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤
  │                          │    Si 429 : retry max 3× sur tous les providers                 │
  │                          │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤
  │                          │                       │                       │                    │
  │                          │                       │◄──────────────────────────────────────────┤
  │                          │                       │     response text    │                    │
  │                          │                       │                       │                    │
  │                          │                       │  _parse_files()      │                    │
  │                          │                       │  _write_project()    │                    │
  │                          │                       │  record_success()   │                    │
  │                          │                       │─────────────────────►│                    │
  │                          │                       │                       │                    │
  │                          │◄─────────────────────│                       │                    │
  │                          │   {success, files,    │                       │                    │
  │                          │    provider, calls}   │                       │                    │
  │  JSON Response           │                       │                       │                    │
  │◄─────────────────────────│                       │                       │                    │
  │                          │                       │                       │                    │
```

## Composants

### 1. `rate_limiter.py` — Gestionnaire de providers

Gère l'état de chaque provider LLM avec une machine à états :

```
                    ┌─────────────┐
                    │  AVAILABLE   │
                    └──────┬──────┘
                           │
               ╔═══════════╪═══════════╗
               ║   429 avec           ║
               ║   retryDelay < 60s   ║   429 avec retryDelay >= 3600s
               ║                      ║   ou quota journalier dépassé
               ▼                      ▼
        ┌──────────────┐     ┌────────────────┐
        │ RATE_LIMITED  │     │ QUOTA_EXCEEDED  │
        │ (cooldown:    │     │ (cooldown: 24h) │
        │  retryDelay)  │     └────────────────┘
        └──────┬───────┘              │
               │ cooldown expiré      │ 24h écoulé
               ▼                      ▼
        ┌─────────────────────────────────┐
        │          AVAILABLE                │
        └─────────────────────────────────┘
```

**Classes :**
- `LimiterState` — Énumération `AVAILABLE`, `RATE_LIMITED`, `QUOTA_EXCEEDED`
- `ProviderState` — État individuel d'un provider (compteurs daily/minute, cooldown)
- `ProviderManager` — Gestionnaire central, sélection du meilleur provider

**Ordre de priorité des providers :**

| Priorité | Provider | RPM | TPD | Clé API |
|----------|----------|-----|-----|---------|
| 1 | `gemini/gemini-2.5-flash` | 5 | 1 500 | `GEMINI_API_KEY` |
| 2 | `gemini/gemini-3-flash-preview` | 30 | 1 500 | `GEMINI_API_KEY` |
| 3 | `gemini/gemini-2.5-flash-lite` | 10 | 20 | `GEMINI_API_KEY` |
| 4 | `groq/llama-3.3-70b-versatile` | 30 | 100 000 | `api_key_LLM` |
| 5 | `groq/mixtral-8x7b-32768` | 30 | 100 000 | `api_key_LLM` |

### 2. `config.py` — Création des LLM

Deux fonctions utilitaires :
- `has_key(model)` — Vérifie si la clé API du provider est présente dans `.env`
- `create_llm(model)` — Instancie un `LLM` CrewAI (GeminiCompletion ou LiteLLM)

### 3. `single_generator.py` — Génération mono-call

**Prompt système :**
```
You are a Spring Boot expert. Generate a complete Java Spring Boot application.
Return ALL files using:
<<<FILE:path/to/file.java>>>
[content]
<<<END_FILE>>>
```

**Pipeline de génération :**
1. Vérification du cache (SHA256 du prompt utilisateur)
2. Si cache hit → retour immédiat
3. Sélection du meilleur provider disponible via `ProviderManager.get_best()`
4. Appel LLM unique : `llm.call(prompt)`
5. Parsing du format `<<<FILE:path>>>...<<<END_FILE>>>`
6. Écriture des fichiers sur disque
7. Mise en cache du résultat
8. Retour JSON avec `project_id`, `files`, `provider`, `llm_calls`

**Gestion des erreurs :**
- 429 avec retryDelay < 60s → attendre, retry
- 429 quota journalier → marque `QUOTA_EXCEEDED` (24h), passe au provider suivant
- Erreur non-429 → retour immédiat avec message d'erreur
- Max 3 tentatives globales (tous providers confondus)

### 4. `Server.py` — API REST

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Informations générales, statistiques |
| `/generate` | POST | Générer un projet Spring Boot |
| `/health` | GET | État des providers, statistiques d'appels |
| `/projects` | GET | Liste des projets générés |
| `/download/{id}` | GET | Télécharger le ZIP du projet |
| `/admin/reset` | GET | Réinitialiser le cache et les compteurs |

## Structure des fichiers générés

```
output/proj_{timestamp}_{suffix}/
├── pom.xml
├── src/main/java/com/example/{project}/
│   ├── {Project}Application.java
│   ├── controller/
│   │   └── {Entity}Controller.java
│   ├── service/
│   │   └── {Entity}Service.java
│   ├── repository/
│   │   └── {Entity}Repository.java
│   ├── entity/
│   │   └── {Entity}.java
│   └── dto/
│       └── {Entity}DTO.java
└── src/main/resources/
    └── application.properties
```

## Système de cache

- Clé : `SHA256(user_prompt)[:32]`
- Valeur : `(project_id, timestamp, response_text)`
- TTL : 2 heures (7200s)
- Nettoyage : automatique à l'insertion

## Statistiques

```python
GET /health → {
  "providers": {
    "gemini/gemini-2.5-flash": {
      "state": "AVAILABLE",
      "calls": 5,
      "daily": 5,
      "remaining_daily": 1495,
      "remaining_minute": 3,
      "cooldown_remaining": 0,
      "last_error": null
    }
  },
  "call_stats": {
    "global_calls": 12,
    "request_calls": 1
  }
}
```

## Fichiers du projet

```
src/System_Agentic/
├── __init__.py
├── config.py              # Création LLM, vérification clés API
├── rate_limiter.py        # Machine à états des providers
└── single_generator.py    # Générateur mono-call + cache

src/Server.py              # API FastAPI
ARCHITECTURE.md             # Ce fichier
```

## CLI SpringForge

SpringForge CLI est un outil en ligne de commande qui permet de générer et modifier des projets Spring Boot directement depuis le terminal.

### Installation

```powershell
# 1. Se placer à la racine du projet
cd C:\Users\WALID\Desktop\agentProject

# 2. Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# 3. Installer les dépendances CLI
pip install typer httpx rich -q
```

### Utilisation

#### Raccourci `agent` (batch)

Créez un fichier `agent.bat` dans un dossier de votre PATH (ou utilisez `bin\agent.bat` fourni) :

```batch
@echo off
call "C:\Users\WALID\Desktop\agentProject\.venv\Scripts\activate.bat" >nul
python "C:\Users\WALID\Desktop\agentProject\cli_agent\main.py" %*
```

Ensuite, depuis n'importe où dans un CMD :

```cmd
agent --help
agent health
agent
```

Le dossier `bin\agent.bat` est déjà créé à la racine du projet. Ajoutez `C:\Users\WALID\Desktop\agentProject\bin` à votre PATH ou copiez-le ailleurs.

#### Mode interactif (REPL)

Lancez `agent` sans arguments pour un mode interactif type code agent :

```powershell
# Lancer le mode interactif
python cli_agent\main.py
```

Vous verrez un banner coloré avec les commandes disponibles et un prompt `>>>` :

```text
##############################################
#   SPRINGFORGE CLI     v3.0                 #
# Spring Boot Agentic Generator              #
##############################################
# generate  <description>                    #
# edit      <dir> <changes>                  #
# add       <feature>                        #
# health                                     #
# exit                                       #
##############################################

  >>> generate create a spring boot rest api
  >>> edit ./my-project "add jwt auth"
  >>> health
  >>> exit
```

Tapez directement la commande sans le préfixe `agent`.

#### Mode direct (args)

```powershell
# Afficher l'aide
python cli_agent\main.py --help

# 1. Générer un nouveau projet Spring Boot
python cli_agent\main.py generate "create a user management api with crud"

# 2. Générer dans un dossier spécifique
python cli_agent\main.py generate "blog api" --path C:\Projects

# 3. Modifier un projet existant (via API /edit)
python cli_agent\main.py edit ./mon-projet "add jwt authentication"

# 4. Ajouter une fonctionnalité
python cli_agent\main.py add "payment with stripe" --path ./mon-projet

# 5. Vérifier l'état de l'API backend
python cli_agent\main.py health
```

### Raccourci agent (alias facultatif)

```powershell
# Créer un alias pour utiliser "agent" au lieu de "python cli_agent\main.py"
Set-Alias agent python cli_agent\main.py  # PowerShell
# ou
doskey agent=python cli_agent\main.py $*  # CMD

# Ensuite :
agent generate "rest api with get post put delete"
agent health
```

### Structure du CLI

```
cli_agent/
├── main.py                          # Point d'entrée, parsing des commandes
├── requirements.txt                 # typer, httpx, rich
├── commands/
│   ├── generate.py                  # agent generate "<prompt>"
│   ├── edit.py                      # agent edit <dir> "<changes>"
│   └── add.py                       # agent add "<feature>" --path <dir>
├── core/
│   ├── client.py                    # Client HTTP (retry, download ZIP)
│   └── parser.py                    # Extraction --path, nettoyage prompt
└── utils/
    ├── config.py                    # URL API, timeout, max retries
    └── logger.py                    # Logs colorés (info/success/warn/error/step)
```

## Décisions d'architecture

| Décision | Raison |
|----------|--------|
| **Mono-call LLM** | Réduction de 90% des appels (vs multi-agents CrewAI) |
| **Parsing local** | Évite les appels LLM supplémentaires par fichier |
| **Cache SHA256** | Évite la regénération pour un même prompt |
| **Fallback ordonné** | Priorise les providers avec le plus de quota restant |
| **QUOTA_EXCEEDED ≠ RATE_LIMITED** | Évite les retries inutiles sur un quota journalier épuisé |
| **Stateless** | 1 requête = 1 réponse = 1 projet complet |
| **Format <<<FILE:path>>>** | Simple à générer par le LLM, fiable à parser |
