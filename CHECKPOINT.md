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

Código enviado e conferido em [wesleyvieira99/AgenticEngeneering](https://github.com/wesleyvieira99/AgenticEngeneering). A revisão executável verificada é `e2d711173726ee546b2a45614c4cd1c2acbeebcf`; atualizações posteriores registram evidências e fixam o runner Ubuntu24.04.

**CI remota e Pages bloqueados externamente, sem nenhum step executado.** O GitHub informou: “The job was not started because your account is locked due to a billing issue.” [CI](https://github.com/wesleyvieira99/AgenticEngeneering/actions/runs/39507360102) · [Pages](https://github.com/wesleyvieira99/AgenticEngeneering/actions/runs/39507595610). A URL Pages respondeu404, portanto o manual **não foi publicado**. Não confundir os testes locais aprovados com CI remota aprovada. [Registro estruturado](docs/evidence/github-publication.json).

Pages está configurado para Actions e os workflows estão preparados. Publicação por branch também depende de Actions, conforme documentação oficial. Nenhuma configuração financeira da conta foi alterada.

## Bloqueios externos

- GitHub CI/Pages: o proprietário precisa resolver o bloqueio de cobrança da conta. Não se trata de falha nos testes, pois o runner não iniciou.

- Bedrock/LiteLLM pagos: credenciais temporárias/endpoint, acesso ao modelo e tabela de preços aprovados.
- Langfuse externo: endpoint, credenciais e confirmação de recebimento.
- AWS deploy: orçamento/autorização específicos e recursos-base parametrizados (VPC, RDS, secret, ECR e certificado).
- Produção pública: substituir autenticação de laboratório por OIDC, migrações versionadas, retenção/backups e avaliação em escala.

## Próximo passo concreto

Depois de liberar Actions na conta, executar `gh workflow run ci.yml --repo wesleyvieira99/AgenticEngeneering --ref main`. A conclusão bem-sucedida na branch principal publica o manual. Conferir os dois runs, abrir a URL e atualizar este checkpoint. Enquanto isso: `make manual-dev` serve o manual local sem credenciais.

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
