# Atlas API contract v1
All paths under `/api`; Bearer token required except health and login. Tenant is derived from token, never trusted from request data. JSON unless indicated. Errors use FastAPI `{detail: ...}`. CORS permits localhost clients only by default.

- GET /api/health -> `{status, mode}`
- POST /api/auth/login `{tenant, username, password}` -> `{access_token, token_type, tenant, role}`. Local demo tenants acme and orbit; username admin; password from ATLAS_DEMO_PASSWORD (default atlas-local-only; development only).
- GET /api/documents -> array `{id,title,version,created_at}`
- POST /api/documents JSON `{title, content}` (browser reads UTF-8 .txt/.md) -> document. Max 1 MiB. DELETE /api/documents/{id}.
- POST /api/runs `{question, strategy, conversation_id?, memory_enabled?:false}` -> `{id,status}`. Strategies: baseline,direct,rag,cag,agent,langgraph,multiagent,async.
- GET /api/runs -> array runs.
- GET /api/runs/{id} -> `{id,status,question,strategy,answer,sources:[{id,title,text,score}],events:[{type,data}],usage:{input_tokens,output_tokens,cost_usd,model},latency_ms,approval_id?,conversation_id?,error?}`
- GET /api/runs/{id}/events -> SSE: `event: <type>\ndata: <JSON>\n\n`; types status, token `{text}`, sources array, approval object, usage object, done run, error `{message}`. Fetch with Authorization header; reconnect by polling run. Events are auditable execution events, no private reasoning.
- POST /api/runs/{id}/cancel -> run
- POST /api/runs/{id}/resume -> run (only failed/cancelled; no automatic repeated effect)
- GET /api/approvals -> array `{id,run_id,action,arguments,status}`
- POST /api/approvals/{id}/approve `{}` -> `{status,ticket_id?}`
- POST /api/approvals/{id}/reject `{}` -> `{status}`
- GET /api/tickets -> array `{id,title,status,created_at}`
- GET /api/usage -> `{input_tokens,output_tokens,cost_usd,runs,limits}`
- GET /api/settings -> limits object; PUT /api/settings -> limits object (admin only)
- DELETE /api/conversations/{id} -> `{deleted:true}`

Independent clients use VITE_API_URL / runtime API base default http://localhost:8000. No provider secrets in clients. Manual runs entirely offline with no API and labels demonstrations as simulations.
