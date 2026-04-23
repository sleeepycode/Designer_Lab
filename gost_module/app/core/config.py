from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / 'storage'
DOCUMENTS_DIR = STORAGE_DIR / 'documents'
EXPORTS_DIR = STORAGE_DIR / 'exports'
STATE_DIR = STORAGE_DIR / 'state'

for path in (STORAGE_DIR, DOCUMENTS_DIR, EXPORTS_DIR, STATE_DIR):
    path.mkdir(parents=True, exist_ok=True)
