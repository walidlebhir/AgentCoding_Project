import os
from dotenv import load_dotenv

# Seul vestige de CrewAI dans l'architecture actuelle (v3).
# On importe uniquement la classe LLM pour bénéficier de son abstraction unifiée :
#   - Préfixe "gemini/" → utilise LiteLLM pour Gemini
#   - Préfixe "groq/"   → utilise LiteLLM pour Groq
# Les anciens composants CrewAI (Agent, Crew, Task, Tool) ont été supprimés car
# l'approche multi-agent consommait 12 à 40 appels LLM par projet, causant des
# erreurs 429 par épuisement des quotas gratuits.
from crewai import LLM

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

from src.System_Agentic.rate_limiter import PROVIDER_CONFIG


def has_key(model: str) -> bool:
    cfg = PROVIDER_CONFIG.get(model)
    if not cfg:
        return False
    return bool(os.getenv(cfg["key_var"]))


def create_llm(model: str) -> LLM | None:
    cfg = PROVIDER_CONFIG.get(model)
    if not cfg or not has_key(model):
        return None
    key = os.getenv(cfg["key_var"])
    # CrewAI LLM gère automatiquement le routage vers le bon fournisseur
    # via le préfixe du model name ("gemini/" ou "groq/").
    return LLM(model=model, api_key=key, temperature=0.2)
