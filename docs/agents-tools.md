# Catálogo de agentes e ferramentas

Definição operacional: uma função executa uma transformação determinada pelo código; uma chamada LLM gera uma saída; um workflow escolhe transições programadas; um agente usa uma decisão do modelo para escolher ações dentro de limites e observa seus resultados. O modo determinístico simula decisões para testar software. Uma função com nome de especialista não vira agente por causa do nome.

| Papel | Responsabilidade/contrato | Ferramentas | Conclusão |
|---|---|---|---|
| supervisor | Até dois especialistas e síntese; orçamento do run compartilhado | Delegação limitada | Resultados coletados ou falha explícita |
| researcher | Evidência autorizada, fontes e rascunho estruturado no modo real | documents.search | Fontes e JSON válidos dentro do orçamento |
| analyst | Resumo factual dos tickets e análise estruturada no modo real | tickets.list | Dados autorizados e saída limitada |
| executor | Preparar TicketArguments e aprovação exata | tickets.propose | Aprovação persistida, sem executar antes do humano |
| reviewer | Validar schema e pertencimento das citações | Nenhuma | IDs existentes; groundedness não comprovada automaticamente |

Definições: `packages/agents/contracts.py`; implementações por papel em `packages/agents/*/agent.py`; instruções e montagem de chamadas em `packages/orchestration/engine.py` e `packages/context/assembly.py`; configuração em `Limits`/ambiente; testes em `tests/backend`. O perfil agent usa um ToolPlan com allowlist. O perfil multiagent usa fan-out/fan-in com no máximo dois especialistas e uma síntese. Funções de revisão/política continuam determinísticas para que modelo nenhum conceda autoridade.

| Ferramenta | Leitura/escrita | Autorização e efeito |
|---|---|---|
| documents.search | Leitura | Tenant do token, modelo de embedding compatível |
| tickets.list | Leitura | Apenas tickets do tenant |
| tickets.propose | Preparação de escrita | operator/admin; grava aprovação vinculada à ação |
| aprovação REST | Escrita | Admin, digest/validade, unicidade, grava um ticket |

## MCP

Servidor real: `python -m packages.mcp.server`. Host configura `ATLAS_API_URL`, `ATLAS_MCP_TOKEN` e `ATLAS_MCP_SCOPES`. Padrão de scopes: `tickets:read,documents:read`; para propor, adicionar `tickets:write` e usar identidade operator/admin. Token é credencial de sessão; não colocar em arquivo versionado. A ferramenta de escrita prepara aprovação e não expõe aprovação automática.

O SDK anuncia tools `tickets_list`, `documents_list`, `tickets_propose`, resource `atlas://security-policy` e prompt `grounded_question`. O transporte implementado é stdio: processo filho, JSON-RPC em stdout, logs em stderr. Streamable HTTP é explicado no manual mas não publicado por este servidor. MCP não é autorização automática nem um protocolo de delegação entre agentes; API REST continua sendo o ponto de aplicação da política.
