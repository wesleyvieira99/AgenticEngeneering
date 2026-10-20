"""Own isolated subprocesses; never terminate an existing listener."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]


def wait(url, process):
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        if process.poll() is not None:raise RuntimeError(f'Server exited for {url}')
        try:
            with urllib.request.urlopen(url,timeout=1) as r:
                if r.status==200:return
        except Exception:time.sleep(.2)
    raise TimeoutError(url)


def main():
    ports={key:free_port() for key in ['api','react','angular','manual']}
    env=os.environ.copy()
    # Explicit deterministic/hermetic test configuration; no paid fallback.
    env.update(ATLAS_MODE='deterministic',ATLAS_MODEL='deterministic-extractive-v1',ATLAS_PRICE_VERSION='local-zero-inference-v1',ATLAS_INPUT_USD_PER_MILLION='0',ATLAS_OUTPUT_USD_PER_MILLION='0',ATLAS_ENV='development',ATLAS_EMBEDDING_MODE='hash',ATLAS_TOKEN_SECRET='isolated-e2e-secret-at-least32-characters',ATLAS_DEMO_PASSWORD='atlas-local-only',
               ATLAS_CORS_ORIGINS=','.join(f'http://127.0.0.1:{ports[k]}' for k in ['react','angular']))
    processes=[]
    (ROOT/'artifacts').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        env['DATABASE_URL']='sqlite:///'+temp+'/e2e.db'
        commands=[('api',[sys.executable,'-m','uvicorn','services.api.main:app','--host','127.0.0.1','--port',str(ports['api'])]),
            ('react',[sys.executable,'-m','http.server',str(ports['react']),'--bind','127.0.0.1','--directory','apps/web-react/dist']),
            ('angular',[sys.executable,'-m','http.server',str(ports['angular']),'--bind','127.0.0.1','--directory','apps/web-angular/dist/browser']),
            ('manual',[sys.executable,'-m','http.server',str(ports['manual']),'--bind','127.0.0.1','--directory','apps/manual/dist'])]
        try:
            for key,command in commands:
                log=open(ROOT/f'artifacts/e2e-{key}.log','w')
                process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
                processes.append((process,log))
                wait(f'http://127.0.0.1:{ports[key]}'+('/api/health' if key=='api' else '/'),process)
            env.update(ATLAS_E2E_API=f'http://127.0.0.1:{ports["api"]}',ATLAS_REACT_URL=f'http://127.0.0.1:{ports["react"]}',ATLAS_ANGULAR_URL=f'http://127.0.0.1:{ports["angular"]}',ATLAS_MANUAL_URL=f'http://127.0.0.1:{ports["manual"]}')
            subprocess.run(['npm','test','--prefix','tests/e2e'],cwd=ROOT,env=env,check=True)
        finally:
            for process,log in processes:
                process.terminate()
            for process,log in processes:
                try:process.wait(timeout=8)
                except subprocess.TimeoutExpired:process.kill();process.wait()
                log.close()


if __name__=='__main__':main()
