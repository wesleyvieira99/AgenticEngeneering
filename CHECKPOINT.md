# Atlas — checkpoint

Atualizado em 20/10/2026. O repositório foi encontrado vazio e implementado em commits separados por backend, laboratórios/infraestrutura, manual, clientes e integração.

## Funciona e foi testado

- API multi-tenant, documentos, fontes, memória consentida, ferramentas, tickets persistidos e aprovação idempotente.
- Oito perfis; LangGraph com checkpoints; worker persistente; gateway com reserva compartilhada e rejeição de configuração divergente.
- Inferência e embeddings reais via Ollama + PostgreSQL/pgvector. Streaming observado antes de terminar em quatro estratégias.
- MCP stdio real com proposta/consulta e autorização na API.
- 33 testes backend; avaliações determinísticas; dois clientes com builds/testes; manual de 28 capítulos ligado ao código; nove cenários Chromium.
- LoRA smoke e modelo pré-treinado executados; evidências numéricas e limitações registradas.
- Terraform init/validate sem erros, sem plan/apply.

## Publicação

Código enviado e conferido em [wesleyvieira99/AgenticEngeneering](https://github.com/wesleyvieira99/AgenticEngeneering). O [manual está publicado](https://wesleyvieira99.github.io/AgenticEngeneering/) e respondeu HTTP 200. Pages informa `status: built`, com fonte `gh-pages`, diretório `/` e `build_type: legacy`.

- Fonte da primeira publicação verificada: `bafce1f469b507e27f6fd74b08595ccd135b5d4f`.
- Commit dessa primeira publicação em `gh-pages`: `b3aad0e36b681aacde1d51802d896a093deffafd`.
- [Primeira execução de publicação concluída](https://github.com/wesleyvieira99/AgenticEngeneering/actions/runs/39516397350): `39516397350`.
- [CI personalizada](https://github.com/wesleyvieira99/AgenticEngeneering/actions/runs/39515853377): `39515853377`, bloqueada por cobrança antes de executar qualquer step. A publicação bem-sucedida não comprova aprovação dessa CI.

A publicação usa artefatos estáticos já compilados e `.nojekyll`. A [exceção documentada pelo GitHub](https://github.blog/changelog/2024-07-08-pages-legacy-worker-sunset/) foi verificada nesta conta: esse caminho publicou mesmo com a CI personalizada indisponível. A afirmação anterior de que mudar para branch nunca ajudaria estava incompleta. Nenhuma configuração financeira foi alterada e nenhum recurso pago foi criado. [Registro estruturado](docs/evidence/github-publication.json).

A revisão atualmente servida pode ser conferida no [manifest público](https://wesleyvieira99.github.io/AgenticEngeneering/manifest.json); o registro acima preserva a primeira publicação verificada.

## Bloqueios externos

- GitHub CI personalizada: o proprietário precisa resolver o bloqueio de cobrança para executar os workflows de testes. O runner não iniciou; o manual publicado em Pages está disponível.

- Bedrock/LiteLLM pagos: credenciais temporárias/endpoint, acesso ao modelo e tabela de preços aprovados.
- Langfuse externo: endpoint, credenciais e confirmação de recebimento.
- AWS deploy: orçamento/autorização específicos e recursos-base parametrizados (VPC, RDS, secret, ECR e certificado).
- Produção pública: substituir autenticação de laboratório por OIDC, migrações versionadas, retenção/backups e avaliação em escala.

## Próximo passo concreto

Para novas versões do manual, executar build e validação em uma revisão limpa, copiar `apps/manual/dist/.` — incluindo `.nojekyll` — para um clone da branch `gh-pages`, fazer commit e push normal, sem force. Seguir os comandos em [deploy](docs/deploy.md), acompanhar a publicação e verificar a URL e o manifest públicos.

A retomada da CI personalizada é independente: após resolver a cobrança, executar os testes remotos. Para voltar à publicação automática por workflow, alterar antes Pages para `build_type: workflow` e então disparar a CI na branch `main`. `make manual-dev` continua disponível para estudo local.

## Comandos de retomada

```sh
git status --short
make setup
make verify
make dev
ATLAS_TEST_DATABASE_URL=postgresql+psycopg://atlas:atlas-local-db@localhost:54329/atlas make test-integration
make test-e2e
gh run list --repo wesleyvieira99/AgenticEngeneering
```

Leia `docs/coverage.csv`, `docs/verification.md` e `docs/final-report.md`. Não confundir modo determinístico com inferência real, nem validação Terraform com deploy AWS. `make stop` encerra apenas o Compose do projeto sem apagar o volume.
