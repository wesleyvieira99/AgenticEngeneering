# Relatório de entrega Atlas

Entrega implementada e verificada localmente em 20/10/2026. Código enviado ao GitHub e [manual publicado em GitHub Pages](https://wesleyvieira99.github.io/AgenticEngeneering/), com HTTP 200. A publicação usa artefatos pré-compilados na branch `gh-pages` e `.nojekyll`. A CI personalizada permanece bloqueada por cobrança, sem executar os testes no GitHub. Evidência e retomada em [CHECKPOINT.md](../CHECKPOINT.md). O caminho principal é real: API e banco persistem documentos/tickets; Ollama executa inferência e embeddings; os dois clientes usam HTTP e SSE. O manual é estático e não simula um backend.

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

## Primeira publicação verificada

A primeira [execução bem-sucedida, `39516397350`,](https://github.com/wesleyvieira99/AgenticEngeneering/actions/runs/39516397350) publicou o commit `gh-pages` `b3aad0e36b681aacde1d51802d896a093deffafd`, gerado da revisão-fonte `bafce1f469b507e27f6fd74b08595ccd135b5d4f`. Pages informa `built`, fonte `gh-pages` em `/` e `build_type: legacy`. A exceção de publicação estática com `.nojekyll` está [documentada pelo GitHub](https://github.blog/changelog/2024-07-08-pages-legacy-worker-sunset/) e foi confirmada nesta conta.

Sete arquivos públicos tiveram SHA-256 comparado ao build validado, incluindo o manifest; página inicial, capítulo e recarga profunda foram conferidos no navegador.

A [CI personalizada `39515853377`](https://github.com/wesleyvieira99/AgenticEngeneering/actions/runs/39515853377) não iniciou nenhum step por bloqueio de cobrança. Publicação concluída e testes locais aprovados não são apresentados como CI remota aprovada. Nenhuma configuração financeira foi alterada ou recurso pago criado. [Evidência](evidence/github-publication.json) e [procedimento de atualização sem force push](deploy.md).

A revisão atualmente servida consta no [manifest público](https://wesleyvieira99.github.io/AgenticEngeneering/manifest.json); os identificadores acima preservam a primeira publicação verificada.

## O que a entrega não demonstra

Não foi validada uma plataforma pronta para tráfego público, um SLA, qualidade ampla de domínio ou um teto absoluto de toda a fatura cloud. Autenticação ainda é de laboratório; BM25 processa corpus autorizado em memória; retenção/backups e controle de egress de terceiros precisam evolução. O corpus e avaliação são pequenos; a heurística de abstenção é imperfeita. Provedores pagos e Langfuse externo permanecem bloqueados por configuração. Recursos multimodais, GraphRAG, QLoRA e bancos alternativos são conteúdo/extension points, não integrações certificadas.

Consulte `docs/coverage.csv` para distinguir implementado, testado localmente, validado com serviço real, documentado, planejado e bloqueado. As evidências são arquivos reais em `docs/evidence` e resultados de GitHub Actions, não números ilustrativos do manual.
