# Relatório de entrega Atlas

Entrega implementada e verificada localmente em 20/10/2026. Código enviado ao GitHub. CI remota e GitHub Pages foram bloqueados pela conta por cobrança antes de iniciar; o manual funciona localmente. Evidência e retomada em CHECKPOINT.md. O caminho principal é real: API e banco persistem documentos/tickets; Ollama executa inferência e embeddings; os dois clientes usam HTTP e SSE. O manual é estático e não simula um backend.

## Entregas

- API multi-tenant, validação Pydantic, RBAC/ABAC, fontes, contexto, memória opt-in, tickets e aprovações vinculadas à ação exata.
- Oito perfis comparáveis, LangGraph com checkpoints, especialistas limitados, fila e worker, gateway e orçamento compartilhado.
- MCP stdio com ferramentas/resources/prompts e autorização; OTel configurável para Langfuse.
- React e Angular independentes; manual com 28 capítulos e 19 marcos didáticos por capítulo, glossário, busca, progresso/notas/favoritos, quizzes e nove laboratórios interativos.
- Laboratórios numéricos, atenção, LoRA smoke e fine-tuning pequeno realmente executado.
- Compose, Terraform preparado/validado, CI, fontes/versionamento, threat model, ADRs, operação e matriz de cobertura.

## Evidência observada

- 33 testes backend, incluindo PostgreSQL/pgvector real, concorrência, isolamento, injeção e orçamento.
- Streaming HTTP real com Ollama: RAG, agente, multiagente e LangGraph; fragmentos recebidos enquanto a execução ainda estava em andamento.
- Jornada MCP real de proposta, aprovação REST e ticket persistido.
- 32 execuções comparativas determinísticas; três perguntas com resposta conhecida e uma sem evidência por perfil.
- Builds React, Angular e manual, testes dos clientes e nove cenários Chromium; detalhes finais em `docs/verification.md`.
- LoRA pré-treinado executado por oito passos em CPU; Terraform validado sem provisionar recursos.

## O que a entrega não demonstra

Não foi validada uma plataforma pronta para tráfego público, um SLA, qualidade ampla de domínio ou um teto absoluto de toda a fatura cloud. Autenticação ainda é de laboratório; BM25 processa corpus autorizado em memória; retenção/backups e controle de egress de terceiros precisam evolução. O corpus e avaliação são pequenos; a heurística de abstenção é imperfeita. Provedores pagos e Langfuse externo permanecem bloqueados por configuração. Recursos multimodais, GraphRAG, QLoRA e bancos alternativos são conteúdo/extension points, não integrações certificadas.

Consulte `docs/coverage.csv` para distinguir implementado, testado localmente, validado com serviço real, documentado, planejado e bloqueado. As evidências são arquivos reais em `docs/evidence` e resultados de GitHub Actions, não números ilustrativos do manual.
