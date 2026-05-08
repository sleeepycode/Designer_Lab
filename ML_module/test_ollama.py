from ml.config import AI_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL, is_ollama_enabled
from ml.ollama_client import ask_ollama_json
print('AI_PROVIDER:', AI_PROVIDER)
print('BASE_URL:', OLLAMA_BASE_URL)
print('MODEL:', OLLAMA_MODEL)
print('ENABLED:', is_ollama_enabled())
print(ask_ollama_json('Верни строго JSON: {"ok": true}', 'Ты тестовый помощник.'))
