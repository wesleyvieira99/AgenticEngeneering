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

Commits locais criados. Push, CI remota e GitHub Pages em verificação final. Não considerar o site publicado até registrar URL e execução bem-sucedida abaixo.

## Bloqueios externos

- Bedrock/LiteLLM pagos: credenciais temporárias/endpoint, acesso ao modelo e tabela de preços aprovados.
- Langfuse externo: endpoint, credenciais e confirmação de recebimento.
- AWS deploy: orçamento/autorização específicos e recursos-base parametrizados (VPC, RDS, secret, ECR e certificado).
- Produção pública: substituir autenticação de laboratório por OIDC, migrações versionadas, retenção/backups e avaliação em escala.

## Próximo passo concreto

Verificações locais concluídas: 33 testes backend, 15 React, 5 Angular e 9 cenários Chromium aprovados. Fazer push e acompanhar Actions/Pages. Atualizar este checkpoint com links observados.

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
