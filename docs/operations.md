# Operação e incidentes

Antes de iniciar: ler README, selecionar modo, confirmar segredo e banco. `make dev` sobe Compose; `make stop` preserva volume. `make seed` carrega corpus sintético. `/api/health` confirma modo, não prova inferência. Execute smoke para testar jornada. Logs do processo não devem conter prompts nem tokens de autenticação.

| Sintoma | Investigar | Ação segura |
|---|---|---|
| API não conecta ao banco | `docker compose -f infra/local/compose.yml ps`; URI e porta | Restaurar conectividade; não apagar volume |
| 409 modelo de embedding | Metadados do índice versus configuração | Fazer backup e `POST /api/documents/reindex`; não comparar vetores incompatíveis |
| 429 persistente | Reservas abertas, fila e limite global | Identificar run/causa; reconciliar cobranças ambíguas |
| Run async permanece queued | Worker ativo, mesmo DATABASE_URL/segredo/modelo | Subir worker; reentrega usa ID persistido |
| Provedor responde mas run falha | Schema JSON, IDs de fontes, max_output, contagem | Inspecionar tipo de erro e uso; ampliar limite só após diagnóstico |
| Aprovação expirada/adulterada | Digest e validade | Preparar nova ação; não editar aprovação antiga |
| Fluxo interrompido | Estado de run e checkpoint | Resume somente quando seguro; efeito idempotente não deve duplicar |

## Observabilidade

Eventos públicos registram autorização, contexto, ferramentas, fontes, uso e estado. Não são pensamento privado do modelo. Spans OTel correlacionam tenant/run/modelo. Para Langfuse: configure endpoint OTLP e cabeçalho Basic no ambiente do **servidor**, a partir de secret, e teste uma trace sintética. Consulte https://langfuse.com/integrations/native/opentelemetry . Configuração sem recebimento confirmado não conta como integração validada.

## Rollout, rollback e recuperação

Fixe imagem pelo digest; execute migração e testes em banco de staging; faça backup PostgreSQL com `pg_dump` usando credencial via secret/.pgpass; registre versão do schema, prompt, modelo e índice. Restaure em banco novo e rode smoke antes de trocar tráfego. O Terraform ECS habilita circuit breaker com rollback; isso não reverte schema ou efeitos de negócio. Preserve compatibilidade de leitura durante rollout. Mudar modelo de embedding exige reindexação, não apenas trocar env.

Não foi realizado exercício de disaster recovery em AWS nesta entrega. Em produção, testar RPO/RTO, restauração point-in-time, disponibilidade multi-AZ, rotação de credenciais, alertas de fila/erro/custo e retenção legal são gates explícitos.
