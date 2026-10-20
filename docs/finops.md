# AI FinOps e governança

Medir não é limitar. `usage` descreve consumo observado; alertar informa que um limiar foi cruzado; limite por execução impede um fluxo individual; teto global exige coordenar chamadas em andamento. Atlas reserva a quantidade máxima da execução e seu custo antes de admiti-la, dentro da mesma transação que cria o run. Workers compartilham o banco. A reserva é reconciliada uma vez; timeout ambíguo conserva a reserva até investigação.

A chave de atribuição é tenant/run/modelo, com eventos de agente e ferramenta. Tokens determinísticos são estimados e marcados; Ollama retorna `prompt_eval_count` e `eval_count`; Bedrock retorna `inputTokens`/`outputTokens`; LiteLLM fornece `usage` do contrato compatível. Custos locais de inferência são zero dólares de API, **não** zero eletricidade/hardware. Custos reais só são calculados com preços explicitamente configurados e versionados. Não há preço comercial inventado.

## Configuração

No servidor: `ATLAS_PRICE_VERSION` identifica data, provedor, região, modelo e tabela. `ATLAS_INPUT_USD_PER_MILLION`/`ATLAS_OUTPUT_USD_PER_MILLION` são preços aprovados pelo operador. Perfis pagos falham na inicialização se a tabela faltar. A API `/api/settings` controla tokens globais e por run, saída, chamadas, ferramentas, passos, tempo e concorrência. Apenas admin altera. O painel distingue consumo e reservas. `successful_runs` conta execuções com estado `completed`, inclusive abstenções; o custo por sucesso mostrado é custo por conclusão técnica. Uma taxa de sucesso semântico exige avaliação de qualidade adicional.

## Garantias e limites

O ledger serializa admissão e reserva sob PostgreSQL; o teto vale para recursos modelados no ledger. Não é um teto garantido da fatura AWS: impostos, cache cobrados diferentemente, reasoning tokens, embeddings pagos, chamadas feitas fora do gateway, retries do proxy, batch e alteração de preços exigem categorias adicionais e reconciliação com billing. O projeto desativa retry automático do adaptador Bedrock e não configura fallback pago. O limite estimado de contexto não é o tokenizer de todos os provedores: confirmar contagem nativa e margem conservadora antes de prometer teto rígido.

O LiteLLM proxy pode centralizar modelos, mas seu limite de spend não substitui reserva global. A documentação oficial exige banco para budgets e descreve comportamento sem banco; a aplicação mantém ledger independente. Fonte verificada em 2026-10-20: https://docs.litellm.ai/docs/proxy/users .

## Diagnóstico

Se 429: consulte active_runs/reserved_tokens/used_tokens; não aumente o teto automaticamente. Se processo caiu após enviar a chamada: correlacione request ID e relatório do provedor, confirme cobrança, registre decisão e só então reconcilie. Reiniciar o processo não prova que não houve cobrança. Não edite contadores para “destravar” sem evidência. Para custo por tarefa bem-sucedida, divida custo total incluindo falhas pelo número de critérios de sucesso satisfeitos, não apenas por respostas HTTP200.

## Experimentos

Compare baseline, RAG e CAG no mesmo dataset; observe recall, groundedness e latência, não apenas preço. Reduza contexto, use modelo menor ou cache e execute novamente os mesmos testes reservados. Um ganho de velocidade com regressão de resposta não é ganho líquido. Batching altera throughput e tempo de espera; fila com taxa de chegada acima da capacidade não estabiliza só aumentando timeout.
