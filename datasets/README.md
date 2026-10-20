# Dados Atlas

Todos os arquivos deste diretório foram escritos para este projeto em 2026-10-20. Pessoas, organizações, incidentes, regras e valores são **sintéticos**, sem dados de clientes. O autor do projeto dedica estes dados ao domínio público via CC0-1.0. Código do repositório: MIT. Modelos externos conservam suas próprias licenças.

`corpus.json` é corpus operacional comum a RAG e CAG. `eval.jsonl` contém perguntas reservadas para avaliação (não prompts de desenvolvimento). `tuning/*.jsonl` tem splits separados por exemplo; corpus pequeno não sustenta alegações de generalização. Não use perguntas de teste para escolher hiperparâmetros.
