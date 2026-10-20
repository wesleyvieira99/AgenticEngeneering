# ADR 0003 — Publicação estática separada da aplicação
Data: 2026-10-20. Status: aceito.

GitHub Pages serve o manual com rotas hash sob /AgenticEngeneering/. API, workers e banco rodam via Compose/local ou ECS. Os clientes aceitam a URL da API; nenhuma credencial de provedor entra em bundles. Não há backend fictício em Pages. A CI não exige credenciais de modelos e distingue testes de contrato de uma chamada real.
