import requests
from ml.config import OLLAMA_BASE_URL, OLLAMA_MODEL, is_ollama_enabled

def ask_ollama_json(prompt: str, system_prompt: str = 'Ты полезный AI-анализатор учебных отчётов.') -> str:
    if not is_ollama_enabled():
        raise RuntimeError('Ollama is not enabled. Set AI_PROVIDER=ollama.')
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {'model': OLLAMA_MODEL, 'stream': False, 'messages': [{'role': 'system', 'content': system_prompt + ' Отвечай только валидным JSON без markdown.'}, {'role': 'user', 'content': prompt}], 'options': {'temperature': 0.2}}
    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()
    return response.json()['message']['content']
