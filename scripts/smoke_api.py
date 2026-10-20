"""Exercise real HTTP journeys, preserving evidence without bearer credentials."""
import argparse
import json
import os
from pathlib import Path
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--mode', choices=['deterministic', 'real'], default='deterministic')
    parser.add_argument('--output', default='artifacts/http-smoke.json')
    args = parser.parse_args()
    client = httpx.Client(base_url=args.url, timeout=120)
    health = client.get('/api/health').json()
    assert (health['mode'] != 'deterministic') if args.mode == 'real' else (health['mode'] == 'deterministic')
    def login(tenant):
        r = client.post('/api/auth/login', json={'tenant': tenant, 'username':'admin', 'password': os.getenv('ATLAS_DEMO_PASSWORD','atlas-local-only')})
        r.raise_for_status()
        return {'Authorization':'Bearer '+r.json()['access_token']}
    acme, orbit = login('acme'), login('orbit')
    for doc in json.loads((ROOT/'datasets/corpus.json').read_text()):
        r=client.post('/api/documents',headers=acme,json=doc);r.raise_for_status()
    def run(question, strategy):
        r=client.post('/api/runs',headers=acme,json={'question':question,'strategy':strategy});r.raise_for_status()
        run_id=r.json()['id']
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            value=client.get('/api/runs/'+run_id,headers=acme).json()
            if value['status'] in ('completed','failed','cancelled','awaiting_approval'):
                return value
            time.sleep(.2)
        raise TimeoutError(run_id)
    result=run('Qual o prazo de primeira resposta para um incidente P1?', 'rag')
    assert result['status']=='completed',result
    assert result['sources'],result
    assert client.get('/api/runs/'+result['id'],headers=orbit).status_code==404
    stream=client.get('/api/runs/'+result['id']+'/events',headers=acme)
    assert stream.status_code==200 and 'event: done' in stream.text
    action=run('/ticket Verificar incidente P1 sintético', 'agent')
    assert action['status']=='awaiting_approval',action
    approval='/api/approvals/'+action['approval_id']+'/approve'
    assert client.post(approval,headers=orbit,json={}).status_code==404
    first=client.post(approval,headers=acme,json={});first.raise_for_status()
    second=client.post(approval,headers=acme,json={});second.raise_for_status()
    assert first.json()['ticket_id']==second.json()['ticket_id']
    report={'health':health,'mode_validation':args.mode,'rag':result,'action':action,
            'ticket':first.json(),'checks':['HTTP login','ingestion','answer with retrieved sources','SSE events','tenant isolation','approval isolation','idempotent ticket'],
            'quality_note':'Smoke validates plumbing and constraints, not broad semantic correctness.'}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps({'status':'passed','provider':health['mode'],'ticket_id':first.json()['ticket_id'],'evidence':str(path)}))


if __name__=='__main__':
    main()
