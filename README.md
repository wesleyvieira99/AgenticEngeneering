# AgenticEngeneering · Atlas

**Uma plataforma de conhecimento e operações com IA, acompanhada por um manual interativo em português.** O nome deste repositório é intencionalmente `AgenticEngeneering`.

[Manual local](apps/manual/README.md) · [Matriz de cobertura](docs/coverage.csv) · [Evidências](docs/verification.md) · [Retomada](CHECKPOINT.md)

Atlas tem API FastAPI, documentos por tenant, busca híbrida com pgvector, respostas com fontes, streaming, memória opt-in, oito perfis de arquitetura, gateway de modelos, limites, fila persistente e criação real de tickets com aprovação/idempotência. React e Angular são clientes independentes. O manual funciona sem chaves e contém 28 capítulos, quizzes, anotações, progresso exportável, código real e simuladores identificados.

**Publicação:** código enviado; GitHub Actions e Pages bloqueados pela conta do GitHub antes de iniciar os jobs. [Evidência e retomada](docs/deploy.md). O manual funciona localmente com `make manual-dev`; a URL Pages ainda não está publicada.

## Começar: modo determinístico

Pré-requisitos: Git, Python **3.12**, Node **24.3.0** e Docker Compose v2. Reserve aproximadamente 3GB de disco para dependências/imagens, 4GB RAM para API/banco/clientes. O modo determinístico não chama LLM.

No terminal:

```sh
git clone https://github.com/wesleyvieira99/AgenticEngeneering.git
cd AgenticEngeneering
make setup
make dev
make seed
```

Em outro terminal, na mesma raiz:

```sh
npm run dev --prefix apps/web-react
# Ou, em outro terminal:
npm run dev --prefix apps/web-angular
```

Abra React em `http://localhost:5173` ou Angular em `http://localhost:4200`. API em `http://localhost:8000`, OpenAPI em `/docs`. Login local: organização `acme`, usuário `admin`, senha `atlas-local-only`. `viewer` lê; `operator` propõe operações; somente `admin` aprova. `orbit` demonstra isolamento. Estas identidades são de laboratório; não exponha o login demo na internet.

Pergunte “Qual o prazo de primeira resposta para um incidente P1?”. Inspecione fontes e eventos. Para atualizar um documento, envie o novo conteúdo com o mesmo título: somente a versão mais recente participa da busca. Envie `/ticket Investigar incidente P1`, abra Aprovações e aprove. Repetir a aprovação mantém um único ticket no banco. Use `/tickets` para consultar.

Encerre clientes com Ctrl+C e banco/API/worker com `make stop`; o volume permanece. Se a porta8000 estiver ocupada, `ATLAS_API_PORT=8010 make dev`, selecione essa URL no login e use `ATLAS_API_URL=http://localhost:8010 make seed`.

### Sem Docker

Após `make setup`, execute `make api` (SQLite local); em outro terminal `make worker`; então `make seed`. Esse caminho testa a aplicação, mas não valida pgvector nem concorrência PostgreSQL. O manual é independente: `make manual-dev`, abra `http://localhost:4173`.

## Inferência local real

Instale Ollama a partir do projeto oficial. O perfil verificado utiliza Ollama0.40.6, `qwen2.5:0.5b` (aprox.398MB, Apache-2.0) e `all-minilm` (aprox.46MB, 384dimensões). Modelo pequeno: útil para validar integração, qualidade limitada. Recomendação de laboratório: 8GB RAM; execução desta entrega ocorreu em Apple Silicon24GB. Não é requisito de GPU cloud.

```sh
ollama serve
# outro terminal:
ollama pull qwen2.5:0.5b
ollama pull all-minilm
ATLAS_MODE=ollama ATLAS_MODEL=qwen2.5:0.5b ATLAS_EMBEDDING_MODE=ollama make dev
ATLAS_API_URL=http://localhost:8000 make seed
.venv/bin/python scripts/smoke_api.py --mode real
```

Se houver chunks hash de um teste anterior, faça login e `POST /api/documents/reindex` com Bearer. O servidor rejeita misturar embeddings incompatíveis. Os digests utilizados estão em `docs/evidence/ollama-models.json`; tags podem mudar, verifique antes de reindexar. No Linux, configurar `host.docker.internal:host-gateway` ou endpoint acessível do Ollama; nunca abra11434 na internet.

## Provedor e Bedrock

`ATLAS_MODE=litellm` usa proxy compatível; `ATLAS_MODE=bedrock` usa Converse via credencial temporária do ambiente. Configure modelo, região e tabela de preço versionada; não coloque chaves no navegador. Veja [deploy](docs/deploy.md), [FinOps](docs/finops.md) e `.env.example`. Teste de contrato não comprova acesso real ao provedor. AWS não foi provisionada.

## Verificar e aprender

```sh
make test                # API, contratos, MCP, clientes e matemática do manual
make evaluate            # 8 perfis × dataset sintético; relatório em artifacts/
make docs-build          # manual + links internos + snippets reais
make clients-build       # React e Angular
make test-e2e            # Chromium, servidores isolados, jornadas e responsividade
ATLAS_TEST_DATABASE_URL=postgresql+psycopg://atlas:atlas-local-db@localhost:54329/atlas make test-integration
make verify              # conjunto principal sem cloud
```

Os [laboratórios](labs/README.md) incluem representação/gradiente, atenção PyTorch e LoRA smoke/pré-treinado. [Evidências](docs/verification.md) distinguem testes executados, qualidade observada e limitações. Simuladores de custo/token/contexto não são benchmarks. A formação exige executar exercícios e defender decisões; não promete domínio apenas pela leitura.

## Organização

- `apps/manual`: capítulos, visualizações e build estático para GitHub Pages.
- `apps/web-react`, `apps/web-angular`: clientes reais do contrato HTTP.
- `services/api`, `services/worker`: HTTP e execução assíncrona.
- `packages`: contratos, agentes, contexto, retrieval, memória, ferramentas/MCP, gateway, FinOps, segurança e observabilidade.
- `labs`, `datasets`, `tests`, `scripts`: reprodução e avaliação.
- `infra/local`, `infra/aws`: Compose e Terraform sem apply automático.
- `docs`: arquitetura, ADRs, fontes, operação, ameaças, matriz e relatório.

Código MIT; dados sintéticos CC0-1.0. Modelos/dependências mantêm suas licenças. Leia [CONTRIBUTING](CONTRIBUTING.md) antes de alterar os contratos.
