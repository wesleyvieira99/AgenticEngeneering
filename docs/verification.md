# Evidências de execução

Registro da sessão de 2026-10-20. Ambiente: macOS Apple Silicon24GB, Python3.12, Node24.3.0, Docker28.1.1. O repositório começou vazio. Não foram provisionados recursos pagos de cloud.

| Verificação | Resultado observado | Evidência |
|---|---|---|
| Unidade/contratos API | Testes de tenant, RBAC, aprovação/digest, memória, reservas, SSE, MCP e graph; contagem no log | [log](evidence/backend-unit.txt) |
| PostgreSQL/pgvector | Extensão0.8.0,384D, admissão concorrente, aprovação concorrente e reentrega | [suite com PostgreSQL](evidence/backend-unit.txt) |
| Jornada HTTP com modelo real | Ollama qwen2.5:0.5b + all-minilm + PostgreSQL; perguntaP1=>15min, tenant negado, ticket idempotente | [registro](evidence/http-real.json) |
| Compose API+worker+banco | Build de imagem Linux e execução real com inferência local | [registro](evidence/compose-real.json) |
| MCP stdio e aplicação real | Leitura → proposta → aprovação REST → ticket no PostgreSQL | [registro](evidence/mcp-real.json) |
| Streaming real progressivo | Quatro estratégias; primeiro fragmento com run ainda running | [registro](evidence/backend-ollama.json) |
| Comparação arquitetural |32execuções determinísticas; mesmo corpus/4perguntas; retrieval e geração separados | [dados](evidence/evaluation.json) |
| Fundamentos numéricos | UTF8/binário/quantização/softmax/entropia/gradiente calculados | [JSON](evidence/foundations.json) |
| Atenção PyTorch | Máscara causal, normalização, equivalência à primitiva PyTorch e gradiente finito | [JSON](evidence/attention.json) |
| LoRA smoke | Pesos aleatórios pequenos; atualização e checkpoint verificados | [JSON](evidence/tuning-smoke.json) |
| LoRA pré-treinado | SmolLM2-135M,8passosCPU,230400parâmetros treináveis; perdas registradas | [JSON](evidence/tuning-full.json) |
| Terraform | init/validate, zero erros/avisos; não houve plan/apply | [JSON](evidence/terraform-validate.json) |
| React/Angular | Builds de produção; 15 testes React e 5 Angular; limites e reservas visíveis | [relatório](clients.md) |
| Chromium desktop/mobile | 9 cenários: jornadas, cancelamento/retomada, troca de tenant, estudo e nove laboratórios | [log](evidence/e2e.txt) |
| Manual | 28 capítulos, 19 pontos/capítulo, 12 snippets e 108 linhas sincronizadas | [build](evidence/manual-build.txt) |
| Fontes externas | 42/42 URLs acessíveis no momento da verificação; não é garantia de disponibilidade futura | [auditoria](evidence/source-check-summary.json) |
| GitHub CI/Pages | Estado remoto registrado após execução | [checkpoint](../CHECKPOINT.md) |

## Qualidade e limites da evidência

A avaliação tem quatro perguntas sintéticas. Recall@5/MRR são calculados somente quando existe documento esperado. O perfil direct não recupera documentos por definição, então recall0 não é regressão. Checagem de substring não equivale a verificação factual. Teste determinístico mede fluxo e restrições, não qualidade de um modelo nem latência representativa de inferência. O benchmark foi usado para diagnosticar falhas: fontes eram descartadas no perfil multiagent, e perguntas sem evidência recebiam trechos irrelevantes. Foram adicionadas prioridade de fontes e heurística de cobertura; os testes passaram a detectar esses casos. Isso não constitui avaliação independente de generalização: o holdout deve ser renovado após essas correções.

No teste real, o modelo de0,5B chegou a responder um prazo errado quando omitia retrieval. O fluxo passou a exigir evidência para consulta de conhecimento e a se abster quando insuficiente. Validação de schema e IDs não garante que toda afirmação seja verdadeira. O relatório do backend registra limitações atuais.

LoRA: perda de validação passou de4,3405 para4,0573 nos três exemplos; teste3,7408. Não é prova de ganho útil, pois n é minúsculo e o smoke foi de oito passos. O experimento foi executado; não é resultado simulado.

## Não executado

- Inferência paga Bedrock/LiteLLM: faltam credenciais/endpoint, acesso ao modelo e preços aprovados.
- Recebimento externo Langfuse: faltam endpoint e credenciais.
- AWS plan/apply/deploy, carga de produção, restauraçãoRDS e SLA: não autorizados/sem ambiente apropriado.
- QLoRA GPU, dataset amplo, multimodal, GraphRAG, índices alternativos: material e backlog; sem alegar implementação.

As imagens de navegador em `docs/evidence` mostram estado sintético local. `artifacts` contém resultados regeneráveis e é ignorado pelo Git; o subconjunto relevante foi copiado para este registro.
