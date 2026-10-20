"""Actual MCP stdio -> authenticated HTTP -> persisted approval -> ticket journey."""
import asyncio
import json
import os
from pathlib import Path
import sys
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]

async def main():
    url=os.getenv('ATLAS_API_URL','http://127.0.0.1:8000')
    with httpx.Client(base_url=url,timeout=30) as client:
        response=client.post('/api/auth/login',json={'tenant':'acme','username':'admin','password':os.getenv('ATLAS_DEMO_PASSWORD','atlas-local-only')});response.raise_for_status()
        token=response.json()['access_token'];headers={'Authorization':'Bearer '+token}
        parameters=StdioServerParameters(command=sys.executable,args=['-m','packages.mcp.server'],cwd=str(ROOT),env={'PATH':os.environ['PATH'],'ATLAS_API_URL':url,'ATLAS_MCP_TOKEN':token,'ATLAS_MCP_SCOPES':'tickets:read,documents:read,tickets:write'})
        async with stdio_client(parameters) as (read,write):
            async with ClientSession(read,write) as session:
                initialized=await session.initialize()
                metadata=await session.list_tools()
                documents=await session.call_tool('documents_list',{})
                assert not documents.isError
                proposal=await session.call_tool('tickets_propose',{'title':'Verificação MCP sintética'})
                assert not proposal.isError
                run_id=json.loads(proposal.content[0].text)['id']
                for _ in range(100):
                    run=client.get('/api/runs/'+run_id,headers=headers).json()
                    if run['status'] not in {'queued','running'}:break
                    await asyncio.sleep(.1)
                assert run['status']=='awaiting_approval', run['status']
                approval=client.post('/api/approvals/'+run['approval_id']+'/approve',headers=headers,json={});approval.raise_for_status()
                tickets=await session.call_tool('tickets_list',{})
                assert not tickets.isError and 'Verificação MCP sintética' in str(tickets.content)
                report={'transport':'stdio','protocol':initialized.protocolVersion,'server':initialized.serverInfo.name,'tools':[t.name for t in metadata.tools],'read_ok':True,'proposal_awaited_human_approval':True,'ticket':approval.json(),'scope_policy':'tickets:write permits proposal only; REST approval still required'}
                (ROOT/'docs/evidence/mcp-real.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
                print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':asyncio.run(main())
