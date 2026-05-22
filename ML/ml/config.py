import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / '.env')
MODULE_NAME = 'ofor-ml'
MODULE_VERSION = '9.0-api-ready-local-ai'
AI_PROVIDER = os.getenv('AI_PROVIDER', 'ollama').lower().strip()
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').strip()
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b').strip()
def is_ollama_enabled() -> bool:
    return AI_PROVIDER == 'ollama'
