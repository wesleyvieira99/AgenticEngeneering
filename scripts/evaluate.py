"""Offline comparative evaluation. Measures checks, never labels them semantic truth."""
import json
import tempfile
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
_BOOTSTRAP = tempfile.TemporaryDirectory(prefix='atlas-eval-bootstrap-')
os.environ.update(ATLAS_MODE='deterministic', ATLAS_MODEL='deterministic-extractive-v1',
                  ATLAS_EMBEDDING_MODE='hash', ATLAS_ENV='development',
                  ATLAS_DEMO_PASSWORD='atlas-local-only',
                  ATLAS_TOKEN_SECRET='offline-evaluation-secret-at-least32',
                  ATLAS_PRICE_VERSION='local-zero-inference-v1',
                  ATLAS_INPUT_USD_PER_MILLION='0', ATLAS_OUTPUT_USD_PER_MILLION='0',
                  DATABASE_URL='sqlite:///'+_BOOTSTRAP.name+'/bootstrap.db')
from fastapi.testclient import TestClient
from services.api.main import create_app
from services.worker.main import run_once

ROOT=Path(__file__).resolve().parents[1]


def main():
    tasks=[json.loads(x) for x in (ROOT/'datasets/eval.jsonl').read_text().splitlines()]
    rows=[]
    with tempfile.TemporaryDirectory() as temp:
        app=create_app(f'sqlite:///{temp}/evaluate.db','deterministic')
        with TestClient(app) as c:
            token=c.post('/api/auth/login',json={'tenant':'acme','username':'admin','password':'atlas-local-only'}).json()['access_token']
            h={'Authorization':'Bearer '+token}
            for doc in json.loads((ROOT/'datasets/corpus.json').read_text()):
                r=c.post('/api/documents',headers=h,json=doc);r.raise_for_status()
            limits=c.get('/api/settings',headers=h).json();limits['tenant_tokens']=1_000_000
            c.put('/api/settings',headers=h,json=limits).raise_for_status()
            for strategy in ('baseline','direct','rag','cag','agent','langgraph','multiagent','async'):
                for task in tasks:
                    started=time.perf_counter()
                    r=c.post('/api/runs',headers=h,json={'question':task['question'],'strategy':strategy});r.raise_for_status()
                    if strategy=='async':run_once(app.state.db)
                    run=c.get('/api/runs/'+r.json()['id'],headers=h).json()
                    expected=task.get('expected_title')
                    titles=[s['title'] for s in run['sources']]
                    rows.append({'strategy':strategy,'task':task['id'],'status':run['status'],
                        'retrieval_hit_at_5':expected in titles[:5] if expected else None,
                        'reciprocal_rank':1/(titles.index(expected)+1) if expected in titles else (0 if expected else None),
                        'answer_substring_check':task['answer_contains'].casefold() in run['answer'].casefold() if task.get('answer_contains') else None,
                        'abstention_expected':task.get('expected_abstention',False),
                        'abstained': 'evidência' in run['answer'] and ('suficiente' in run['answer'] or 'Não há' in run['answer']),
                        'duration_ms':round((time.perf_counter()-started)*1000,2),'usage':run['usage'],
                        'error':run['error']})
    summaries=[]
    for strategy in dict.fromkeys(r['strategy'] for r in rows):
        selected=[r for r in rows if r['strategy']==strategy]
        known=[r for r in selected if r['retrieval_hit_at_5'] is not None]
        summaries.append({'strategy':strategy,'completed':sum(r['status']=='completed' for r in selected),
                          'total':len(selected),'recall_at_5':sum(r['retrieval_hit_at_5'] for r in known)/len(known),
                          'mrr':sum(r['reciprocal_rank'] for r in known)/len(known),
                          'abstention_accuracy':sum(r['abstained'] for r in selected if r['abstention_expected']),
                          'mean_latency_ms':sum(r['duration_ms'] for r in selected)/len(selected)})
    report={'mode':'deterministic','embedding':'hash-384-v1','dataset':'datasets/eval.jsonl','dataset_size':len(tasks),
            'limitations':['Small synthetic held-out set','Substring checks are not groundedness scores','Deterministic latency does not estimate LLM latency','Direct baseline has no retrieval by design','No LLM-as-judge used'],
            'summaries':summaries,'rows':rows}
    out=ROOT/'artifacts/evaluation.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(summaries,indent=2))
    assert all(r['status']=='completed' for r in rows), 'Execution regression; inspect artifacts/evaluation.json'
    grounded=[r for r in rows if r['strategy']!='direct']
    assert all(r['retrieval_hit_at_5'] for r in grounded if r['retrieval_hit_at_5'] is not None), 'Known-document retrieval regression'
    assert all(r['answer_substring_check'] for r in grounded if r['answer_substring_check'] is not None), 'Known-answer content regression'
    assert all(r['abstained'] for r in grounded if r['abstention_expected']), 'Unknown-query abstention regression'


if __name__=='__main__':main()
