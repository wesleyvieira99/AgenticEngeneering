# ADR 0002 — Dados recuperados não são instruções
Data: 2026-10-20. Status: aceito.

Problema: um documento pode conter ordens para ignorar permissões, exfiltrar segredos ou executar operações. Escolha: separar sistema/pergunta/dados, validar schema da resposta, verificar IDs de citações contra fontes recuperadas, manter permissões e mutações no código do servidor e exigir intenção explícita + aprovação para tickets.

Consequências: prompt defensivo reduz risco mas não é autorização. Mesmo texto plausível só vira efeito depois de validação, política e transação. Uma citação existente não prova que todas as frases foram sustentadas; avaliação humana e de groundedness permanecem necessárias. Gateway não faz fallback pago automático e conserva reserva em erro ambíguo.
