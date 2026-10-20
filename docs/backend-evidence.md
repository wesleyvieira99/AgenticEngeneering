# Backend Atlas: implementação, evidências e limites

Verificado em **20 de outubro de 2026**, Python 3.12, macOS ARM64. O código executável está em `services/` e `packages/`; o conjunto de dependências exato está em `requirements.lock`. Versões são um conjunto compatível fixado, não uma afirmação de que todas são as últimas publicadas.

## Caminho executável

Na raiz do repositório:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/uvicorn services.api.main:app --port 8000
# Outro terminal, mesma raiz e variáveis de ambiente:
.venv/bin/python -m services.worker.main
```

`DATABASE_URL` seleciona SQLite portátil ou `postgresql+psycopg://...`. PostgreSQL é o caminho principal: extensão vector, vetores com 384 dimensões e índice HNSW cosseno. Inicialização usa advisory lock transacional para API/worker concorrentes. O usuário do banco inicial precisa criar a extensão; em produção, faça migrações com papel separado antes de reduzir privilégios.

Login local: tenant `acme` ou `orbit`, usuário `admin`, senha `ATLAS_DEMO_PASSWORD` (padrão de desenvolvimento `atlas-local-only`). Há também `operator` e `viewer`, com a mesma senha de bootstrap; isso é um provedor didático, não um sistema corporativo de identidades. Senhas são armazenadas com scrypt/salt. Tokens assinados por HMAC expiram em uma hora e revalidam papel/usuário no banco. `ATLAS_ENV=production` rejeita chave curta/padrão e senha padrão. Alterar a variável de bootstrap não redefine usuários já persistidos.

O primeiro fluxo: autenticar → POST documento → POST execução RAG → ler SSE e fontes → consultar uso. Ação: pergunta `/ticket Investigar incidente` → aprovação persistida → administrador aprova → ticket real no banco. `/tickets` é uma consulta determinística de ferramenta. Argumentos externos nunca escolhem tenant nem concedem papel.

## Arquiteturas reais e fronteiras

| Perfil | Mecanismo implementado | Chamadas ao modelo |
|---|---|---|
| baseline | Recuperação híbrida + extratos determinísticos | 0 |
| direct | Gateway + saída Pydantic; sem recuperação | 1 |
| rag | Ingestão/busca/contexto explícitos + geração | 1, ou 0 se faltar evidência |
| cag | Corpus pré-carregado em cache por tenant/versão/TTL; seleção lexical local dentro do cache | 1, ou 0 se faltar evidência |
| agent | Planejador do modelo escolhe ferramentas de leitura validadas; política exige recuperação para conhecimento; síntese e revisão | até 2 |
| langgraph | StateGraph retrieve → assemble → generate_review, LangChain Runnable e saver durável | até 1 |
| multiagent | Supervisor consulta ferramentas, pesquisador e analista geram pareceres em paralelo e sintetizador agrega | até 3 |
| async | Mesmo pipeline RAG em fila SQL persistida, claim transacional por workers | até 1 |

Modelos determinísticos simulam geração e seleção do planejador; o restante — banco, autenticação, índice, ferramentas, orçamento, aprovações, SSE e checkpoint — é real. O modo `ollama` executa as chamadas dos agentes em um modelo local real. Não há um ciclo ilimitado ReAct: o agente é limitado a planejamento de leitura e execução de uma rodada; criação de tickets exige comando do usuário e aprovação humana. O reviewer aplica schema e referência a fontes, **não prova implicação semântica**.

LangGraph usa `SqliteSaver` ou `PostgresSaver`, não apenas eventos que se parecem com checkpoint. A chave é tenant:usuário:execução. Uma falha anterior à chamada cobrável pode continuar do nó pendente; chamadas ambíguas ou tentativas que já tiveram consumo não são reexecutadas automaticamente. A retomada preserva a atribuição de custos; crie nova execução após uma tentativa cobrada. Estado de grafo é apagado junto com a conversa.

## Recuperação, CAG e resposta sem evidência

`packages/retrieval/pipeline.py`: normalização Unicode do conteúdo, SHA256, janelas de 650 caracteres/sobreposição de 100 e chunks com metadados de modelo. O documento lógico é identificado por **tenant + título exato**, após remover espaços nas bordas na API; diferenças de caixa/acentos representam títulos distintos. Deduplicação só reutiliza a versão vigente se ela ainda tiver chunks e seu hash coincidir. Repetir conteúdo sob outro título cria outro documento; restaurar conteúdo histórico ou reenviar após exclusão cria uma versão maior.

Uma publicação substitui atomicamente os chunks das versões anteriores do mesmo título, preserva os metadados históricos e invalida o cache do tenant. RAG, consulta vetorial, CAG, reindexação e listagem selecionam exclusivamente a maior versão. O filtro também exclui chunks antigos que já existiam antes dessa política; o namespace do cache impede reutilizar entradas legadas. O cálculo de embeddings precede a transação de publicação.

DELETE remove os chunks da versão indicada e invalida o cache, mas **retém ID, título, hash, número e data da versão**. A maior versão sem chunks funciona como marcador de exclusão e impede que uma versão anterior volte à busca. Excluir um ID histórico não apaga a versão vigente. Na atualização de uma instalação antiga, chunks históricos já persistidos ficam inacessíveis à recuperação; uma nova publicação desse título os remove. Essa política não é apagamento integral de dados: fontes já copiadas para execuções, memória e checkpoints são snapshots históricos, e consultas já iniciadas podem concluir com seu snapshot anterior. Apagar a conversa é uma operação separada, descrita abaixo; backups exigem retenção própria.

- `ATLAS_EMBEDDING_MODE=hash` produz **features determinísticas não semânticas** `hash-384-v1` para testes.
- `ATLAS_EMBEDDING_MODE=ollama`, `ATLAS_EMBEDDING_MODEL=all-minilm` usa `/api/embed` real e exige exatamente 384 dimensões finitas.
- Alterar modo/modelo não compara vetores incompatíveis: consulta retorna conflito; `POST /api/documents/reindex` faz a migração explícita com verificação de versão do corpus.
- A busca PostgreSQL usa operador cosseno pgvector, combinada com BM25 Python por Reciprocal Rank Fusion. SQLite calcula cosseno exato. BM25 ainda percorre corpus do tenant em memória: adequado ao laboratório, não benchmark de grande escala.
- Uma heurística explícita de cobertura lexical ponderada remove palavras funcionais e penaliza termos da consulta ausentes. `ATLAS_MIN_LEXICAL_COVERAGE=0.30`. Embeddings reais também podem admitir similaridade acima de `ATLAS_MIN_SEMANTIC_SIMILARITY=0.45`. Esses limiares precisam de calibração; não são probabilidades nem garantias de correção.
- CAG é cache de contexto pré-carregado por cinco minutos, não KV cache, cache semântico ou cache de respostas. Máximo explícito de 24 chunks; corpus maior é rejeitado com orientação para RAG.
- Contexto prioriza fontes antes de resultados de ferramentas/histórico. Evidência insuficiente causa abstenção no caminho fundamentado. Direct é deliberadamente não fundamentado para comparação.

O gateway valida os IDs e adiciona citações que faltam no texto quando declaradas validamente. Schema inválido, IDs desconhecidos ou resposta supostamente fundamentada sem citações geram fallback **identificado como extrativo**, preservando metering da chamada. A validação de citações não detecta toda alucinação que usa uma fonte real.

## Streaming, ferramentas e memória

Ollama usa NDJSON nativo: fragmentos completos do campo JSON `answer` geram eventos SSE durante inferência. São provisórios até validação final; `done` contém a resposta autoritativa e pode substituir o preview por fallback. Outros adaptadores atualmente entregam fragmentos depois da resposta completa; não se afirma streaming nativo para LiteLLM/Bedrock. Eventos mostram plano público, ferramentas, estados, fontes e uso; não há exposição de raciocínio privado.

Cobertura específica de streaming:

- `test_partial_json_stream_decoder` verifica texto Unicode, escapes e escape incompleto entre fragmentos.
- `test_provider_native_stream_contract` usa um provedor **controlado**: exige dois callbacks enquanto o iterador ainda não entregou `done`, confere uso final e falha se o gateway tentar ler além do frame terminal. Esse teste comprova o contrato incremental, não uma chamada real.
- `test_provider_stream_without_final_usage_fails_closed` entrega texto parcial e encerra sem uso final; o gateway lança erro, sem inventar contagem. Retenção de reserva em falha ambígua é coberta separadamente pelo teste de falha do provedor.
- `docs/evidence/backend-ollama.json` vem de **HTTP real**, PostgreSQL/pgvector em schema isolado, Ollama e all-minilm. Para RAG, agente, multiagente e LangGraph registra primeiro fragmento SSE, instante de `done`, 31 fragmentos nativos e uma consulta HTTP independente que observou `running` no primeiro fragmento. Isso verifica entrega antes da conclusão, sem depender de buffer do TestClient.
- A evidência cobre rede local e esse modelo; não cobre proxy reverso em produção, Bedrock streaming, fechamento do navegador no meio da geração ou todas as interleavings de cancelamento. O schema temporário e os checkpoints do smoke foram apagados após a coleta.


Aprovação: SHA256 de tenant + execução + ação + argumentos canônicos, validade de 15 minutos, decisão de administrador, transação única para decisão/ticket e unicidade por aprovação. Aprovar repetidamente retorna o mesmo ticket. Um documento contendo `/ticket` não cria intenção de execução.

Memória episódica exige `memory_enabled=true`; é separada por tenant/usuário/conversa e expira em sete dias. DELETE conversa remove memória, texto/fontes/eventos das execuções associadas e checkpoints. Tickets/aprovações são registros de operação separados e não são apagados implicitamente por apagar uma conversa. Backups têm política de retenção própria; configure-a na operação.

MCP real usa SDK **1.9.4** e transporte stdio: handshake, descoberta, tools, resource e prompt. O host fornece `ATLAS_MCP_TOKEN`; o servidor aplica `ATLAS_MCP_SCOPES`. Ferramentas `tickets_list`, `documents_list`, `tickets_propose`; a escrita só prepara aprovação REST. Não existe servidor HTTP MCP remoto implementado neste incremento. O protocolo não concede autorização.

```bash
ATLAS_MCP_TOKEN='<token local de curta duração>' \
ATLAS_MCP_SCOPES='tickets:read,documents:read,tickets:write' \
.venv/bin/python -m packages.mcp.server
```

## FinOps e falhas

Reserva e admissão usam `SELECT ... FOR UPDATE` por tenant em PostgreSQL e `BEGIN IMMEDIATE` em SQLite. Contabilizam tokens, dinheiro e concorrência global no banco compartilhado; não dependem de um contador por processo. Uma execução reserva o máximo antes de começar. Planejador/especialistas/síntese dividem essa mesma reserva; chamadas/ferramentas/passos/timeout também têm limites. Limites são copiados para a execução. A admissão registra uma assinatura de configuração segura (modo, modelo, versão/preços de entrada/saída, versão de embedding e região Bedrock), sem credenciais. Antes de qualquer chamada, o worker compara sua configuração com essa assinatura: divergência falha sem inferência e libera a reserva ainda não utilizada. A assinatura não congela os pesos por trás de uma tag mutável de modelo; pin/verifique digests no provedor.

`ATLAS_INPUT_USD_PER_MILLION`, `ATLAS_OUTPUT_USD_PER_MILLION` e `ATLAS_PRICE_VERSION` são obrigatórios em modos pagos; os dois preços devem ser estritamente positivos. Preços não são descobertos automaticamente. Ollama tem custo de inferência do provedor igual a zero; isso **não mede energia, hardware ou operação**. A estimativa conservadora por bytes limita contexto, e uso do provedor reconcilia a reserva.

Timeout, stream incompleto ou falha de worker após início não implicam ausência de cobrança. Reserva permanece bloqueada; não há retry/fallback cobrável implícito. O operador resolve com evidência do provedor:

```bash
.venv/bin/python -m packages.finops.reconcile RUN_ID \
  --input-tokens 100 --output-tokens 40 --cost-usd 0.001 \
  --evidence-id provider-request-id
```

Esse comando exige acesso administrativo ao banco; os números do exemplo são ilustrativos, não custos medidos. Reentrega só reivindica `queued`; execução já concluída não repete efeitos. Workers abandonados tornam-se `failed` após prazo+30 segundos; reserva permanece até investigação. Depois de três tentativas a retomada entra em dead letter lógico. Não há dashboard dedicado para dead letters nem execução durável arbitrária equivalente a Temporal.

## Evidências de validação

Comandos executados:

```bash
.venv/bin/ruff check packages services tests/backend
.venv/bin/python -m pip check
ATLAS_TEST_DATABASE_URL='postgresql+psycopg://.../atlas' \
  .venv/bin/python -m pytest tests/backend -q
.venv/bin/python scripts/evaluate.py
```

Resultado registrado nesta etapa: **33 testes passaram**, incluindo PostgreSQL real/pgvector, orçamento com seis admissões simultâneas (duas aceitas), aprovação simultânea idempotente, dois workers competindo pela mesma execução, tenant isolation, RBAC, documento adversarial, deduplicação, CAG, memória, LangGraph durável, contrato Converse, stream NDJSON, handshake MCP real, retomada real de nó pendente, abstenção, fallback de citações e rejeição anterior à inferência de deriva de modo/modelo/preço/embedding. Regressões de atualização verificam respostas/citações apenas da versão vigente, invalidação do cache, isolamento entre tenants, retorno a conteúdo histórico como nova versão e exclusão sem ressurreição, inclusive com chunks/cache legados. A integração PostgreSQL repete atualização/exclusão nos caminhos pgvector e CAG. Uma advertência de depreciação do TestClient/AnyIO permanece, sem falhas. A suite pode crescer em revisões subsequentes; consulte a evidência final da CI.

A comparação determinística do corpus sintético executou 32 casos (8 perfis × 4 tarefas). Não confundir acerto em três perguntas conhecidas e uma desconhecida com generalização. Evidências de inferência real são separadas: `docs/evidence/backend-ollama.json` e relatório HTTP principal. Na primeira rodada real, o planejador sem ferramenta levou o modelo pequeno a inventar um prazo; isso motivou política obrigatória de recuperação e a retestagem, em vez de chamar uma execução HTTP bem-sucedida de qualidade validada.

## Limitações e próximos passos explícitos

1. Login local deve ser substituído por OIDC/SSO com gestão real de usuários; rate limit de login é por processo. Isolamento é aplicado na aplicação, sem RLS PostgreSQL neste incremento.
2. Falta benchmark de índices em escala, avaliação semântica abrangente, reranker real/cross-encoder, corpus multimodal, GraphRAG e migração zero downtime de dimensão.
3. Bedrock e LiteLLM têm adaptadores e contratos; credenciais/chamadas pagas não foram usadas nesta etapa. Modelo/região precisam ser verificados para a conta antes de inferência. Preços configurados não equivalem a reconciliação de fatura.
4. OTel exporta metadados; um destino OTLP/Langfuse precisa ser configurado e validado externamente. Não exportamos corpos de documentos, prompts ou senhas.
5. Sem automação de garantia de groundedness; citações válidas ainda podem acompanhar uma interpretação errada. Previews de streaming são provisórios.
6. Mudanças de schema além do bootstrap precisam de migrações versionadas antes de produção. Backup, exclusão em backups, rotação/revogação global de chaves e auditoria externa são trabalho operacional.

## Fontes primárias verificadas

- [FastAPI](https://fastapi.tiangolo.com/) — contratos, dependências e respostas de streaming.
- [pgvector Python](https://github.com/pgvector/pgvector-python) — Vector, cosseno e integração SQLAlchemy.
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) — StateGraph, estado, transições e checkpoint.
- [Ollama chat](https://docs.ollama.com/api/chat) — JSON schema, NDJSON e contagem de tokens.
- [Ollama embeddings](https://docs.ollama.com/api/embed) — `/api/embed`, dimensões e comportamento de truncamento.
- [Bedrock Converse](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html) — payload e permissões de inferência.
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — versão 1.9.4 instalada, assinaturas verificadas e protocolo exercitado pelo teste real. Documentação atual v2 não é usada como contrato deste servidor v1.
