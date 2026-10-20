# Manual Atlas — evidência editorial e técnica

Data de revisão: **20/10/2026**. O manual foi implementado em `apps/manual/`, com saída estática em `apps/manual/dist`. Hospedagem do manual não implica hospedagem da API. Nenhuma credencial de serviço pago é necessária para estudar.

## Entregue

- 28 capítulos, mais de **14 mil palavras autorais** no conteúdo estruturado, mais explicações de código e interface.
- Cada capítulo apresenta os 19 pontos pedidos: problema, pré-requisitos, definição simples/técnica, mecanismo, exemplo, matemática, implementação, arquivos/linhas, execução, verificação, diagnóstico, trade-offs, impactos, exercício, solução, entrevista, fontes e conclusão verificável.
- 35 termos português/inglês, trilhas por nível, pré-requisitos ligados, breadcrumbs e links permanentes de seção.
- Busca no conteúdo integral dos capítulos; favoritos, notas e progresso locais; exportação/importação JSON validada; 28 quizzes com feedback; soluções reveláveis; cópia de comandos; impressão.
- Nove laboratórios: vetores, atenção, bytes/tokens, contexto, custos, concorrência, gradiente, workflow e comparador dos oito perfis. Todos identificados como cálculos/simulações educativos, sem métricas fictícias de serviços.
- **12 snippets de código real com 107 linhas comentadas**, extraídos de Python e TypeScript. Incluem cosseno, softmax, atenção PyTorch, contexto, reserva/reconciliação, digest de aprovação, RBAC, chunking, identidade do checkpoint, atribuição de uso e parser SSE dos clientes.
- Tema claro/escuro, layout responsivo, navegação por teclado, foco visível, link de pular conteúdo, respeito a `prefers-reduced-motion` e CSS de impressão.

## Verificações executadas pelo responsável pelo manual

```sh
python3 apps/manual/build.py
python3 apps/manual/validate.py
node --check apps/manual/app.js
node apps/manual/math.test.mjs
```

Resultado: **aprovado**. A validação comprova 28 IDs únicos, todos os campos pedagógicos, grafo acíclico de pré-requisitos, existência dos caminhos de código, correspondência exata/hash dos snippets e seus arquivos, explicações por linha, assets e manifest, sintaxe JavaScript e propriedades numéricas. Os testes cobrem dimensões inválidas, vetor zero, softmax estável, máscara causal, soma dos pesos, UTF-8, excesso de contexto, custo, concorrência ideal e convergência/divergência de gradiente.

Esses comandos **não comprovam** execução de cloud, acessibilidade integral por auditoria especializada ou desempenho de produção. A execução E2E e as capturas desktop/mobile são conduzidas na integração final, com resultados separados em `docs/evidence/`. Consulte o relatório de E2E e entrega para o estado final, em vez de inferir validação visual deste texto.

## Conexão com implementação

O manual usa os caminhos reais `packages/retrieval/pipeline.py`, `packages/context/assembly.py`, `packages/security/auth.py`, `packages/tools/registry.py`, `packages/finops/budget.py`, `packages/model_gateway/gateway.py`, `packages/orchestration/engine.py`, `services/api/`, clientes e labs. O capítulo de fine-tuning cita a execução real limitada de 8 passos com SmolLM2-135M-Instruct registrada em `docs/evidence/tuning-full.json`; a queda de loss em três exemplos de validação não é apresentada como generalização útil.

Fontes são documentação oficial e artigos originais. A equipe de integração executa a auditoria de links em `docs/evidence/sources.json`. O comparador de pgvector/Qdrant/OpenSearch/Milvus é qualitativo; não afirma equivalência nem benchmark não executado.

## Limitações explícitas

- Progresso mede autodeclaração e quizzes locais, não certificação. Backup depende de exportação do usuário.
- O explorador vetorial usa 2D; atenção usa uma query e duas posições; gradiente usa regressão escalar. Eles demonstram mecanismos e não substituem modelos de produção.
- Contagem de tokens no navegador é estimada por bytes/fator. Custo usa preços ilustrativos; concorrência usa ondas ideais de tarefas uniformes.
- Conteúdo didático descreve tanto implementação quanto extensões, deixando essa diferença explícita. Suporte multimodal, GraphRAG, cross-encoder, OPA, índices alternativos e serviços cloud exigem as etapas/evidências próprias.
- URLs externas podem mudar; o build local não faz rede. A auditoria externa é separada para não confundir reprodução offline com disponibilidade momentânea de terceiros.
