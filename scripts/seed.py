"""Load only the project synthetic corpus through authenticated API."""
import json
import os
from pathlib import Path
import httpx
url=os.getenv('ATLAS_API_URL','http://localhost:8000')
with httpx.Client(base_url=url,timeout=60) as c:
    r=c.post('/api/auth/login',json={'tenant':'acme','username':'admin','password':os.getenv('ATLAS_DEMO_PASSWORD','atlas-local-only')});r.raise_for_status()
    headers={'Authorization':'Bearer '+r.json()['access_token']}
    for doc in json.loads(Path('datasets/corpus.json').read_text()):
        result=c.post('/api/documents',headers=headers,json=doc);result.raise_for_status()
        print('Documento carregado:',doc['title'])
