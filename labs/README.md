# Laboratórios reproduzíveis

Execute na raiz do repositório, com Python 3.12. Os resultados observados estão em `docs/evidence/`, não são previsões.

1. **Representação e ML**: `python3 labs/foundations/main.py`. Sem dependências. Imprime UTF-8, binário, quantização int4 didática, softmax, entropia, cosseno e descida do gradiente. Verifique soma de probabilidades = 1 e MSE decrescente. Experimento: troque temperatura de 1 para 2; a distribuição deve ficar menos concentrada. Falha de dimensão: compare comprimentos dos vetores.
2. **Atenção**: crie `python3.12 -m venv .venv-labs`, instale `.venv-labs/bin/pip install -r labs/requirements.lock` e execute `.venv-labs/bin/python labs/attention/main.py`. Cerca de 1 GB de disco para ambiente; CPU e 2 GB RAM suficientes. Compara QKᵀ/√d, máscara e softmax com a operação PyTorch, verifica derivadas. Remova a máscara e observe acesso ao futuro. Isso não treina um LLM.
3. **LoRA smoke**: `.venv-labs/bin/python labs/finetuning/train.py --output artifacts/tuning-smoke`. Sem downloads de pesos. Usa transformer minúsculo inicializado aleatoriamente; testa máscara do prompt, splits, backward, pesos adaptados e checkpoint. Não representa fine-tuning de modelo pré-treinado.
4. **LoRA pré-treinado**: `.venv-labs/bin/python labs/finetuning/train.py --full --steps 8 --output artifacts/tuning-full`. Baixa SmolLM2-135M-Instruct, revisão fixada no código, Apache-2.0, aproximadamente 550 MB. CPU, 4 GB RAM e 2 GB disco; macOS/Linux. Dataset CC0 sintético (8/3/3); métricas não demonstram generalização. Custo cloud zero; energia/tempo local não estimados. Compare perdas antes/depois, não apenas o texto gerado. Para treinos maiores: orçamento e hardware precisam de experimento medido.
5. **RAG, CAG e arquiteturas**: `make evaluate` inicia a API em processo de teste, usa o mesmo corpus e perguntas para todos os perfis e grava métricas separadas de retrieval/geração. Inferência é determinística neste comando. Para modelo real use o quickstart e `scripts/smoke_api.py --mode real`.
6. **Segurança e idempotência**: `make test`. Localize os testes de tenant, aprovação e reservas. Altere uma regra em branch própria e demonstre que o teste falha; reverta antes de publicar.
7. **Vetores, contexto, concorrência e custos**: `make manual-dev`; use Laboratórios no manual. São simulações educativas sem credenciais, não benchmarks.

Solução comentada da atenção: a máscara faz posições futuras receberem −∞; exp(−∞)=0, então o próximo token não contamina o presente. Remover √d aumenta magnitude dos logits com a dimensão e pode saturar softmax. `backward` calcula a derivada do escalar em relação a Q, não atualiza pesos; isso exige um otimizador.

Para limpar, remova apenas `artifacts/` ou os ambientes criados neste guia. Não apague volumes PostgreSQL para encerrar o serviço; `make stop` preserva dados.
