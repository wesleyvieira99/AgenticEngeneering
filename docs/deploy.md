# Deploy: manual e aplicação

## GitHub Pages

A workflow Pages publica `apps/manual/dist`. Usa rotas hash, assets relativos e índice estático no caminho exato `/AgenticEngeneering/`. O build extrai snippets do código real. Pages não executa Python, não guarda documentos e não é backend dos clientes. Veja status da Action e abra a URL publicada antes de declarar publicação concluída.

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
