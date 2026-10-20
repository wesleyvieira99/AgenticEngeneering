# Deploy: manual e aplicação

## GitHub Pages

O [manual está publicado](https://wesleyvieira99.github.io/AgenticEngeneering/) e foi verificado com HTTP 200. Pages serve o artefato estático `apps/manual/dist`, com rotas hash, assets relativos e índice no caminho exato `/AgenticEngeneering/`. O build extrai snippets do código real. API, workers e banco têm hospedagem separada; Pages não os executa.

### Estado verificado em 20/10/2026

A publicação usa a branch `gh-pages`, diretório `/`, com `.nojekyll`; a API do GitHub informa `build_type: legacy` e `status: built`. A [execução `39516397350`](https://github.com/wesleyvieira99/AgenticEngeneering/actions/runs/39516397350) terminou com sucesso. Essa primeira publicação utilizou o commit `b3aad0e36b681aacde1d51802d896a093deffafd`, gerado da revisão-fonte `bafce1f469b507e27f6fd74b08595ccd135b5d4f`. [Evidência dessa primeira publicação](evidence/github-publication.json). A revisão atualmente servida consta no [manifest público](https://wesleyvieira99.github.io/AgenticEngeneering/manifest.json).

A [CI personalizada `39515853377`](https://github.com/wesleyvieira99/AgenticEngeneering/actions/runs/39515853377) continua bloqueada pela cobrança da conta, sem nenhum step executado. Não confundir o sucesso de publicação com aprovação dos testes nessa CI. Os testes locais e o build do manual foram executados separadamente.

A afirmação anterior de que publicação por branch não poderia ajudar estava incompleta. O [changelog oficial do GitHub](https://github.blog/changelog/2024-07-08-pages-legacy-worker-sunset/) documenta a exceção: uma branch com `.nojekyll` pode publicar diretamente arquivos estáticos previamente compilados quando Actions está indisponível. Esse caminho foi confirmado nesta conta. Nenhuma configuração financeira foi alterada e nenhum recurso pago foi criado.

### Atualizar o manual publicado

Execute na raiz de uma cópia limpa da revisão-fonte que deseja publicar, com Python 3.12, Node e Git instalados. O diretório temporário abaixo é um clone separado, dedicado somente à publicação. Preserve o `.nojekyll` do build e não copie código do backend ou segredos.

```sh
# Confirme revisão e ausência de alterações locais antes do build.
git status --short
git rev-parse HEAD
make docs-build
source_revision=$(git rev-parse HEAD)
deploy_dir=$(mktemp -d "${TMPDIR:-/tmp}/atlas-pages.XXXXXX")
git clone --single-branch --branch gh-pages https://github.com/wesleyvieira99/AgenticEngeneering.git "$deploy_dir"
cp -a apps/manual/dist/. "$deploy_dir/"
git -C "$deploy_dir" status --short
git -C "$deploy_dir" add .
git -C "$deploy_dir" commit -m "docs: publish manual from $source_revision"
git -C "$deploy_dir" push origin gh-pages
```

Se não houver diferença no artefato, não há novo commit a publicar. Revise arquivos removidos ou renomeados no build para que não permaneçam desnecessariamente na branch. Não use force push. Após o push, acompanhe a publicação do Pages, abra a URL e compare `manifest.json` e a revisão em `data.json` com o build local. Um push concluído, sozinho, não comprova deploy. Remova o clone temporário somente depois de concluir a verificação.

### Retomar workflows após resolver a cobrança

O workflow `Publish manual` permanece preparado como alternativa. Para voltar a esse caminho, primeiro configure Pages como **GitHub Actions** (`build_type: workflow`); só depois execute a CI na `main`:

```sh
gh workflow run ci.yml --repo wesleyvieira99/AgenticEngeneering --ref main
gh run list --repo wesleyvieira99/AgenticEngeneering
```

Com CI aprovada, o workflow de publicação usa a mesma revisão verificada. Acompanhe os dois resultados e confira novamente a URL. Os runners dos workflows personalizados estão fixados em Ubuntu 24.04; a execução da CI remota ainda não foi validada. Até essa mudança, mantenha a fonte atual `gh-pages` e atualize os artefatos pelo procedimento acima. Para servir localmente: `make manual-dev`.

## Local com Compose

Na raiz: copie `.env.example` para `.env`, mantenha segredos locais, execute `docker compose -f infra/local/compose.yml --env-file .env up --build --wait -d`. API8000, PostgreSQL54329; ambos bind localhost. Suba React5173/Angular4200 separadamente. Para parar: `docker compose -f infra/local/compose.yml down` (sem `-v`). Se8000 estiver em uso, configure mapeamento/porta sem encerrar processos alheios.

## AWS — IaC preparada, sem provisionamento

`infra/aws` é módulo Terraform1.13.3/AWS6.16.0 para ECS Fargate API+worker, ALB interno TLS, roles temporárias, Secrets Manager, CloudWatch e regras de rede. Requer VPC/subnets privadas em duas AZ, RDS PostgreSQL16 com extensão vector habilitada, grupo de segurança do DB, certificado ACM e ECR image digest. Esses recursos existentes são parâmetros explícitos: o módulo não cria silenciosamente uma rede/RDS cobrados. API usa o mesmo ledger/fila PostgreSQL; SQS seria uma alternativa, não um serviço fictício já integrado.

1. Instale Terraform1.13.3 e autentique via AWS IAM Identity Center/role temporária; nunca grave access keys no Git.
2. `terraform -chdir=infra/aws init -backend=false` e `terraform -chdir=infra/aws validate` não provisionam. Validar sintaxe não valida conta, disponibilidade ou deploy.
3. Prepare `.tfvars` ignorado a partir de `terraform.tfvars.example`. Secret existente deve conter DATABASE_URL, ATLAS_TOKEN_SECRET e ATLAS_DEMO_PASSWORD. URI RDS usa TLS (`sslmode=require`), credencial dedicada e pgvector configurado por migration role. A autenticação demo restringe este deploy a laboratório privado; para exposição pública integrar OIDC primeiro.
4. Rede precisa de NAT com política de egress ou VPC endpoints para bedrock-runtime, Secrets Manager, logs, ECR API/DKR e gateway S3 para camadas ECR. DNS privado deve resolver endpoints. Não remova restrições apenas para “fazer funcionar”.
5. Verifique em us-east-1 o modelo amazon.nova-micro-v1:0, acesso da conta e suporte a Converse, quotas e preços. Fonte: https://docs.aws.amazon.com/en_en/bedrock/latest/userguide/model-card-amazon-nova-micro.html (verificação2026-10-20). ID e suporte documentados não provam acesso da conta. Perfil cross-region exige ARNs/permissões de destinos adicionais; este módulo usa in-region.
6. Só depois de orçamento e aprovação específicos: plan revisado, backend remoto de state criptografado/lock, build/push ECR para Linux AMD64 (`docker buildx build --platform linux/amd64 -f infra/local/Dockerfile -t "$ECR_IMAGE" --push .`), fixação do digest publicado em `api_image`, apply. As tasks declaram X86_64; uma imagem ARM64 local não serve para esse perfil. **Nenhum apply foi executado nesta entrega.**

## Serviços gerenciados versus próprios

Bedrock Runtime fornece inferência; Converse uniformiza mensagens para modelos compatíveis, não remove diferenças de recursos. Knowledge Bases pode gerir parsing/retrieval; Agents pode gerir orquestração; Guardrails adiciona políticas de conteúdo. Nenhum deles substitui RBAC do ticket nem idempotência do negócio. Comparar preços por componente, região, tokens e armazenamento; serviços gerenciados reduzem operações e aumentam dependência de contratos AWS. S3 deve ter Block Public Access, criptografia e política por prefixo/tenant se substituir armazenamento de texto no banco. CloudTrail registra APIs de controle; logging de invocação pode conter dados e precisa de política própria.
