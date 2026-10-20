# Atlas — manual interativo

Aplicação estática sem dependências de runtime externas. Usa HTML/CSS, módulos JavaScript nativos e conteúdo autoral em português. Não chama modelos, não guarda credenciais e não simula um backend de produção.

## Executar

Na raiz do repositório, Python 3.12 e Node.js disponíveis:

```sh
python3 apps/manual/build.py
python3 apps/manual/validate.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory apps/manual/dist
```

Abra `http://127.0.0.1:4173/`. Se a porta estiver ocupada, use outra. Equivalente: `make manual-dev`. Encerre o servidor com Ctrl+C. Abrir `index.html` por `file://` não permite fetch de módulos/conteúdo; use HTTP.

A publicação serve **apps/manual/dist**. URLs relativas e rotas hash funcionam no caminho `/AgenticEngeneering/` sem fallback de SPA do servidor:

- `#/inicio`
- `#/capitulo/atlas`
- `#/capitulo/atencao/matematica`
- `#/laboratorios/vectors`
- `#/laboratorios/attention`
- `#/laboratorios/tokens`
- `#/laboratorios/context`
- `#/laboratorios/cost`
- `#/laboratorios/concurrency`
- `#/laboratorios/gradient`
- `#/laboratorios/workflow`
- `#/laboratorios/architectures`
- `#/glossario`, `#/codigo`, `#/estudo`

## Organização

- `content.py`: 28 capítulos com 19 pontos pedagógicos, fontes primárias, pré-requisitos e glossário PT/EN.
- `app.js`: navegação, busca integral, exercícios/quizzes, favoritos, notas, progresso exportável/importável e UI dos laboratórios.
- `math.mjs`: operações numéricas puras. `math.test.mjs` testa propriedades, valores conhecidos e casos de borda.
- `styles.css`: layout responsivo, temas, foco, movimento reduzido e impressão.
- `build.py`: extrai trechos dos arquivos reais Python/TypeScript, registra revisão e SHA-256 e gera dados/manifest.
- `validate.py`: verifica conteúdo, DAG de pré-requisitos, arquivos, hashes, anotações de linhas, assets, sintaxe e matemática.

`data.json` e `dist/` são gerados e ignorados no Git. A revisão usada em links é o commit atual quando a árvore está limpa; no build de uma árvore alterada, a UI identifica isso e oferece links para a branch principal. Não afirmamos que mudanças locais já existem naquele commit.

## Estudo e privacidade

`localStorage['atlas-study-v1']` contém somente tema, IDs de capítulos/favoritos, respostas corretas, notas e último capítulo. O conteúdo do manual é carregado do mesmo host; sem analytics, fontes remotas ou chamadas de IA. Links primários/repositório são abertos pelo usuário.

Exportação baixa JSON. Importação valida versão, IDs e tipos, limita arquivo a 1 MiB e notas a 10.000 caracteres; dados de notas são escapados antes de renderizar. Importação combina listas e substitui notas dos mesmos capítulos. A interface avisa quando armazenamento local não está disponível. Quizzes registram acerto, sem conceder certificação ou afirmar domínio.

## Verificação

```sh
node apps/manual/math.test.mjs
python3 apps/manual/validate.py
```

A validação estática não substitui browser E2E, inspeção visual ou execução de serviços. Evidências de browser e serviços ficam em `docs/evidence/`; o relatório editorial está em `docs/manual-evidence.md`. O build falha quando um snippet muda de quantidade de linhas sem revisar explicações. A validação também compara o conteúdo e hash de cada snippet com o arquivo real.

## Limites dos laboratórios

Vetores/atenção/gradiente executam fórmulas pequenas; tokenização é estimativa por bytes, não tokenizer de produção. Contexto usa contagens fornecidas manualmente. Preços são editáveis e ilustrativos. Concorrência assume duração uniforme e ausência de contenção. Comparador é qualitativo. Workflow é uma sequência educativa sem efeitos externos. Os labs Python/PyTorch e de LoRA reais são ligados aos capítulos e documentados em `labs/README.md`.

### Regressão de busca e navegação

Com as dependências E2E fixadas já instaladas em `tests/e2e`, execute `node apps/manual/browser-regression.cjs`. O teste sobe um servidor estático próprio em porta livre, usa Chromium headless e encerra ambos ao concluir. Verifica Escape com busca preenchida, fechamento de modal ao navegar por hash, clique em resultado, largura mobile e ausência de erros JavaScript. Não usa API nem serviços externos.
