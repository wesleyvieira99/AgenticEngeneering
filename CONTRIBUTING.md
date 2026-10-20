# Contribuir

Leia CHECKPOINT.md, README.md e docs/coverage.csv antes de escolher uma tarefa. Use branch e commit pequeno. Preserve contratos e trabalho alheio. Rode `make verify`, `make test-integration` com PostgreSQL dedicado e `make test-e2e` após alterar fluxos. Execute apenas a verificação pertinente para alterações de texto, além do build/links/snippets.

Toda funcionalidade requer: mecanismo explicado, comando reproduzível, teste que detecte regressão real, limite conhecido e linha na matriz. Não troque “testado localmente” por “validado com serviço real” com mocks. Nunca use chaves/provedores pagos em CI. Dados novos exigem origem/licença; não coloque documentos de clientes em fixtures. Não versione .env, caches, pesos de modelos ou bancos.

Conteúdo fica em apps/manual/content.py; snippets são extraídos dos fontes pelo build. Edite conteúdo autoral, não dist. Fontes devem ser oficiais/primárias com data de consulta. Simplifique termos em PT e preserve termo EN pesquisável. Revisão: verificar acessibilidade, leitura mobile, caminhos sob /AgenticEngeneering/, erros e abandono seguro de operações.
