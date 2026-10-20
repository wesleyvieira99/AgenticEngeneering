"""Optional online source reachability audit; network failures do not invent verification."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/manual'))
from content import SOURCES

def inspect(item):
    key,(title,url)=item
    request=urllib.request.Request(url,headers={'User-Agent':'Atlas educational source verification/1.0'})
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            return {'key':key,'title':title,'url':url,'status':response.status,'final_url':response.url,'checked':date.today().isoformat()}
    except Exception as e:
        return {'key':key,'title':title,'url':url,'status':getattr(e,'code',None),'error':type(e).__name__,'checked':date.today().isoformat()}

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(inspect,SOURCES.items()))
    (ROOT/'docs/evidence/sources.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
    summary={'reachable':sum(r.get('status')==200 for r in results),'total':len(results),'unverified':[r for r in results if r.get('status')!=200]}
    (ROOT/'docs/evidence/source-check-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
    print(json.dumps(summary,indent=2))
