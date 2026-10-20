# Dados Atlas

Todos os arquivos deste diretório foram escritos para este projeto em 2026-10-20. Pessoas, organizações, incidentes, regras e valores são **sintéticos**, sem dados de clientes. O autor do projeto dedica estes dados ao domínio público via CC0-1.0. Código do repositório: MIT. Modelos externos conservam suas próprias licenças.

`corpus.json` é corpus operacional comum a RAG e CAG. `development.jsonl` contém jornadas exploratórias de desenvolvimento. `eval.jsonl` é um arquivo separado de quatro perguntas de regressão, executadas igualmente nos oito perfis. Como suas falhas orientaram correções, ele não é mais um holdout independente: crie uma nova amostra de domínio antes de selecionar modelos ou alegar generalização. `tuning/*.jsonl` tem splits separados por exemplo; corpus pequeno não sustenta alegações de generalização. Não use perguntas de teste para escolher hiperparâmetros.
