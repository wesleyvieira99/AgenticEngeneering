# ADR 0001 — PostgreSQL como fonte de verdade
Data: 2026-10-20. Status: aceito.

Problema: duas execuções ou workers não podem gastar o mesmo orçamento nem criar dois tickets para a mesma aprovação. Cache em memória não coordena processos. Escolha: transações no PostgreSQL, lock por tenant para admissão e reconciliação, IDs persistidos para ação e fila; pgvector mantém filtro de tenant junto dos chunks. SQLite permite testar sem Docker, com serialização restrita a um processo.

Consequências: a API não é suficiente para declarar garantia global sem verificar disputa real de conexões no PostgreSQL. O lock concentra a coordenação de um tenant; particionar no futuro exige preservar invariantes. Redis só entra quando medição demonstrar necessidade, pois duplicar contadores cria reconciliação adicional. RLS é defesa adicional recomendada; filtro explícito na aplicação continua obrigatório e é testado. O usuário do Compose é de desenvolvimento e não é configuração de menor privilégio para produção.
