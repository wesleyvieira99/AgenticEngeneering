# Extensões e gates de produção

O caminho executável e as evidências locais estão entregues conforme verificação. Estes itens não devem ser anunciados como implementados/validados antes dos critérios abaixo.

| Item | Estado | Próximo passo verificável |
|---|---|---|
| AWS/Bedrock com conta real | bloqueado | Informar conta/role/região, acesso ao modelo e orçamento; executar contrato real e registrar usage sem segredo |
| LiteLLM proxy real | bloqueado | Fornecer endpoint/key server-side, modelo e preços aprovados; testar erro/retry/categorias cobradas |
| Langfuse real | bloqueado | Fornecer endpoint e credenciais; confirmar trace recebido e redaction |
| OIDC e usuários reais | planejado | Implementar JWKS issuer/audience, provisioning, revogação; testes de roles e tenant |
| Migrações formais e backup restore | planejado | Alembic + teste banco anterior/atual e restauração em banco novo |
| RLS PostgreSQL e papéis DB mínimos | planejado | Criar roles separadas, SET LOCAL tenant confiável e prova de isolamento com SQL direto |
| Retrieval em corpus grande | planejado | BM25 hoje processa corpus autorizado em memória; medir e mover lexical para índice full-text/BM25 dedicado |
| PDF/OCR/imagem/áudio | documentado | Parser isolado, limites de recursos, dataset licenciado e retrieval multimodal medido |
| GraphRAG e cross-encoder | documentado | Provar necessidade em benchmark; adicionar índice/reranker com custo e licença |
| IVF/PQ e bancos alternativos | documentado | Laboratório de recall/latência no mesmo corpus maior; não alegar equivalência |
| Cache semântico/prefix/KV do provedor | documentado | Separar APIs e preços; validar invalidação e comportamento com serviço escolhido |
| QLoRA em GPU e treino maior | documentado | Hardware adequado, orçamento, dataset maior, licença, validação de memorização e qualidade |
| Categorização integral de billing | planejado | Modelar cache, raciocínio e categorias específicas; reconciliação com fatura e reservas em voo |
| Queue leases/heartbeat e recuperação automática | planejado | Reentrega segura já existe; orfandade exige reconciliação e operador; implementar leases sem duplicar efeitos |
| SQS/Redis/durable engine | documentado | Só introduzir após medição; testar cancelamento e at-least-once |
| Sandboxing/egress de ferramentas de terceiros | planejado | Não há ferramentas shell/URL livre hoje; validar isolamento antes de adicioná-las |
| Avaliação robusta de domínio | planejado | Expandir teste reservado e rubrica humana; medir erro por categoria, não só quatro perguntas |

A abstenção atual usa uma heurística de cobertura lexical além do modelo. Ela pode recusar paráfrases legítimas e aceitar evidência irrelevante com vocabulário similar. Ela reduz um caso de falha observado, não resolve alucinação. O modelo local de0,5B é insuficiente como único decisor para operações críticas.
