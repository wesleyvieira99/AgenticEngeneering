# Versões e fontes verificadas

Data de verificação: **2026-10-20**, fuso America/Sao_Paulo. Versões escolhidas e fixadas para compatibilidade; não se afirma que todas são as mais recentes. O teste de instalação/build é a evidência de compatibilidade no ambiente observado.

| Camada | Versões | Registro reproduzível |
|---|---|---|
| Runtime | Python3.12; Node24.3.0; Docker28.1.1 | ambiente local e workflow |
| API/contratos | FastAPI0.115.12; Pydantic2.11.4; Uvicorn0.34.2 | pyproject.toml / requirements.lock |
| Persistência | SQLAlchemy2.0.41; psycopg3.2.9; pgvector Python0.4.1; extensão0.8.0, PostgreSQL16 | compose imagem por digest |
| Orquestração | LangGraph0.4.5; LangChain Core0.3.60; checkpoint SQLite2.0.10/Postgres2.0.21 | requirements.lock |
| MCP/telemetria | SDK MCP1.9.4; OTel1.33.1; boto3 1.38.23 | requirements.lock |
| React | React19.3.1; Vite8.3.4; TS5.9.3 | package-lock.json |
| Angular | Angular21.2.25; CLI/build21.2.27; TS5.9.3 | package-lock.json |
| Navegador | Playwright1.56.1; Chromium141.0.7390.37 | tests/e2e/package-lock.json |
| Laboratórios | torch2.8.0; transformers4.57.1; peft0.17.1; accelerate1.10.1 | labs/requirements.lock |
| Modelo local | Ollama0.40.6; qwen2.5:0.5b Q4_K_M; all-minilm384D | docs/evidence/ollama-models.json |
| Fine-tuning | SmolLM2-135M-Instruct, revisão12fd25f77366fa6b3b4b768ec3050bf629380bac, Apache-2.0 | labs/finetuning/train.py + tuning-full.json |
| AWS IaC | Terraform1.13.3, AWS provider6.16.0 | .terraform.lock.hcl |

## Fontes primárias e o que sustentam

- https://fastapi.tiangolo.com/ — contratos/dependências/respostas streaming; assinatura confirmada pela execução.
- https://docs.pydantic.dev/latest/concepts/models/ — validação de schemas; pins reais não inferidos do site latest.
- https://github.com/pgvector/pgvector — vetores, HNSW, IVFFlat, filtros e iterative scan0.8. Não confundir índice aproximado com autorização.
- https://docs.langchain.com/oss/python/langgraph/persistence — checkpoints e thread_id; testado contra versões fixadas.
- https://github.com/modelcontextprotocol/python-sdk — FastMCP stdio; capacidades conferidas em handshake real do SDK instalado. O manual apresenta também especificação2025-11-25; isso não significa que SDK1.9.4 negocia toda revisão posterior.
- https://docs.ollama.com/api/chat e https://docs.ollama.com/api/embed — JSON schema, NDJSON, metering e embeddings; chamada real registrada.
- https://docs.litellm.ai/docs/proxy/users — exigência de banco e limites do budget do proxy; não substitui reserva do Atlas.
- https://langfuse.com/integrations/native/opentelemetry — receptor OTLP; configuração documentada, recebimento externo condicionado a credenciais.
- https://docs.aws.amazon.com/en_en/bedrock/latest/userguide/model-card-amazon-nova-micro.html — amazon.nova-micro-v1:0, us-east-1, Converse e disponibilidade documentada; acesso da conta não validado.
- https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-use.html — perfis cross-region e implicações de roteamento; módulo usa in-region.
- https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html — referência para laboratório; resultado comparado numericamente.
- https://huggingface.co/docs/peft/v0.17.0/en/package_reference/lora — LoRA; APIs executadas com0.17.1.
- https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct — modelo/licença/revisão consultada via API oficial.
- https://react.dev/learn e https://angular.dev/reference/versions — APIs dos clientes/compatibilidade; builds reais confirmados.
- https://registry.terraform.io/providers/hashicorp/aws/6.16.0/docs — contratos de recursos; init/validate local, sem plan/apply de conta.

As fontes de cada capítulo aparecem no manual; links servem para aprofundamento. Preços comerciais não foram copiados: o operador deve registrar tabela aprovada para o modelo/região/modalidade utilizados. Uma data de consulta não congela capacidades de um serviço externo.
