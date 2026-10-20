#!/usr/bin/env python3
"""Dependency-free static build, source extraction and manifest. Run from any directory."""
from pathlib import Path
import ast, hashlib, json, shutil, subprocess
from content import CHAPTERS, SOURCES, GLOSSARY
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
DIST=HERE/'dist'
try:
 REV=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
 DIRTY=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True))
except subprocess.CalledProcessError:
 REV='uncommitted'; DIRTY=True
CODE_SPECS=[
('cosine','Similaridade cosseno','labs/foundations/main.py','cosine',['representacao','embeddings'],[
'Entrada: dois vetores a e b. A função devolve um float e não escreve estado externo.',
'Compara comprimentos antes do zip; sem essa verificação, zip truncaria silenciosamente o vetor maior.',
'Recusa dimensões incompatíveis. Sem o erro, um resultado numericamente plausível poderia estar errado.',
'Calcula o produto das normas via soma de quadrados e raiz. Remover a normalização transforma a medida em produto escalar.',
'Soma produtos por coordenada e divide pela norma. Norma zero recebe 0 como sentinela de software; matematicamente o cosseno é indefinido.']),
('softmax','Softmax numericamente estável','labs/foundations/main.py','softmax',['tokens','inferencia','aprendizado'],[
'Entrada: logits e temperatura positiva; saída: lista de probabilidades. Não altera os argumentos.',
'Exige temperatura positiva; zero causaria divisão por zero e negativo inverteria a preferência.',
'Falha explícita torna erro de configuração distinguível de resultado do modelo.',
'Subtrai o maior logit e reescala pela temperatura; evita exponenciais excessivas sem mudar as razões normalizadas.',
'Calcula pesos positivos para cada logit. Ainda não são probabilidades porque não somam necessariamente um.',
'Divide pela soma. Sem esta normalização, interpretar os valores como probabilidades seria incorreto.']),
('attention','Atenção causal em PyTorch','labs/attention/main.py','attention',['atencao'],[
'Recebe Q, K e V e devolve saída e pesos; a operação preserva grafo de autograd e não atualiza parâmetros.',
'Multiplica Q por K transposta e divide por √d. Retirar transpose quebra shapes; retirar escala altera saturação da softmax.',
'Cria máscara booleana triangular acima da diagonal. Sem ela, posições futuras poderiam influenciar o presente.',
'Aplica −∞ às posições futuras e normaliza a última dimensão. Normalizar no eixo errado misturaria queries.',
'Combina valores pelos pesos e também expõe pesos para inspeção. Essa saída não é explicação completa do modelo.']),
('context','Montagem de contexto limitado','packages/context/assembly.py','assemble',['contexto','rag','cag'],[
'Entradas: pergunta, fontes, histórico, resultados e teto. Saídas: mensagens e fontes efetivamente incluídas; sem persistência.',
'Cria envelope de dados externo às instruções confiáveis. Sem separação, ficaria mais fácil confundir texto recuperado com política.',
'Estima tokens dos componentes obrigatórios antes de incluir opcionais; o limite depende do estimador conservador documentado.',
'Rejeita pedido que já excede teto. Truncar a pergunta silenciosamente mudaria o objetivo do usuário.',
'Percorre fontes na ordem recebida; o ranking anterior define prioridade.',
'Cria candidato sem alterar ainda o envelope aceito. Evita perder a última versão que cabia.',
'Testa o candidato contra o teto antes de aceitar. Sem o teste, documentos podem estourar contexto.',
'Aceita somente a versão que cabe e preserva os IDs dos documentos.',
'Percorre resultados de ferramentas depois das fontes; a prioridade é explícita.',
'Prepara envelope candidato com um resultado adicional sem alterar o estado aceito.',
'Verifica se o resultado da ferramenta cabe; sem isso, ferramentas poderiam ultrapassar o teto.',
'Aceita apenas resultados que cabem, evitando truncar o envelope JSON.',
'Limita histórico às últimas quatro entradas e percorre da mais recente para a mais antiga.',
'Prepara adição de histórico preservando ordem cronológica na lista final.',
'Checa o orçamento novamente: histórico compete pelo espaço que sobrou das fontes.',
'Aceita o histórico que cabe. Não é consentimento: a decisão de ler memória acontece antes da função.',
'Retorna instrução em system e dados serializados em user, junto das fontes incluídas para checar citações.']),
('reserve','Reserva antes de executar','packages/finops/budget.py','reserve',['finops','concorrencia'],[
'Entradas: sessão transacional, execução e gateway. Efeitos: altera contadores do tenant e registra reserva no run.',
'Obtém o tenant da execução; não de argumentos livres enviados pelo modelo.',
'Lê política do tenant. A transação do chamador deve proteger concorrência; esta função sozinha não cria lock.',
'Reserva o teto de tokens da execução, para incluir o trabalho previsto dentro dela.',
'Converte teto em custo conservador conforme política versionada do gateway.',
'Verifica vagas antes de criar trabalho. Sem isso, capacidade local não limita o conjunto de workers.',
'Recusa admissão por concorrência com status recuperável 429.',
'Inclui gasto e reservas em andamento no teto de tokens; ignorar reservas permite corrida.',
'Recusa antes de qualquer chamada ao provedor quando saldo de tokens é insuficiente.',
'Compara custo em microunidades com teto monetário; unidade consistente evita erro de um milhão de vezes.',
'Recusa admissão sem saldo monetário. Medir custo depois não impediria o excesso.',
'Bloqueia tokens no saldo compartilhado. A transação externa deve tornar a atualização atômica.',
'Bloqueia custo da chamada, incluindo trabalho ainda não reconciliado.',
'Consome uma vaga concorrente até reconciliação ou liberação segura.',
'Guarda tokens reservados no run para saber quanto retirar da reserva depois.',
'Guarda custo reservado no run para reconciliação exata da intenção.',
'Marca reserva aberta; a reconciliação usará esta flag para evitar duplicação.',
'Copia limites para a execução. Mudanças futuras na política não alteram silenciosamente o snapshot em andamento.',
'Guarda identificadores seguros do gateway e preços, com hash de configuração. Sem esse snapshot, um worker poderia executar com modelo ou preço diferente do usado na reserva; segredos e URLs não entram no snapshot.']),
('reconcile','Reconciliação idempotente','packages/finops/budget.py','reconcile',['finops','workers'],[
'Recebe sessão, run e consumo observado. Atualiza saldo e fecha reserva em uma transação do chamador.',
'Verifica se a reserva continua aberta. Essa guarda permite reentrega do mesmo resultado.',
'Sai sem alterar nada quando o consumo já foi reconciliado.',
'Carrega o tenant associado à execução, preservando atribuição.',
'Retira da reserva o valor originalmente bloqueado em tokens.',
'Retira da reserva monetária o valor originalmente bloqueado.',
'Libera uma vaga após conclusão/reconciliação válida.',
'Acrescenta consumo de entrada e saída observado. Categorias adicionais dependem da política do gateway.',
'Arredonda custo para cima em microunidades, evitando perder frações no ledger.',
'Fecha a reserva; sem esta linha, a reentrega repetiria subtrações e gasto.']),
('digest','Aprovação vinculada à ação','packages/tools/registry.py','action_digest',['agentes','seguranca','mcp'],[
'Recebe tenant, execução, ação e argumentos; devolve hash, sem executar a ação.',
'Serializa campos em ordem estável e sem espaços variáveis. Sem canonicalização, JSON equivalente poderia gerar hashes diferentes.',
'Calcula SHA-256 do payload canônico. O hash detecta divergência, mas a autorização depende também de identidade e armazenamento protegidos.']),
('roles','Autorização por papel','packages/security/auth.py','require_role',['http','seguranca'],[
'Recebe principal confiável e papéis permitidos; o padrão inclui admin e operator.',
'Compara papel derivado da autenticação com a política. Conteúdo de documento não participa dessa decisão.',
'Rejeita com 403 antes do efeito. Remover este PEP deixa o backend depender das escolhas da interface/modelo.']),
('chunks','Chunking fixo real','packages/retrieval/pipeline.py','chunk_text',['ingestao'],[
'Recebe texto, tamanho e overlap em caracteres; não são tokens nem chunking semântico.',
'Documenta o caráter didático e a preservação conceitual de posições; não promete offsets persistidos.',
'Normaliza Unicode e quebras de linha, removendo bordas vazias.',
'Cria janelas com passo size−overlap. A política chama com defaults válidos; parametrização externa deve exigir size>overlap≥0.']),
('checkpoint','Identidade da retomada','packages/orchestration/checkpoints.py','thread_id',['langgraph','multiagente'],[
'Entrada: execução persistida com identidade validada; saída: string para o checkpointer.',
'Combina tenant, usuário e execução. Usar somente um id fornecido pelo cliente permitiria colisão de sessões.']),
('usage','Somar consumo entre etapas','packages/orchestration/engine.py','add_usage',['observabilidade','arquiteturas'],[
'Recebe consumo acumulado e atual e devolve um novo registro.',
'Detecta uma etapa sem chamada e com consumo anterior; evita substituir metadados por um registro vazio.',
'Devolve cópia do consumo anterior, sem produzir uma chamada fictícia.',
'Copia metadados da chamada atual sem alterar o objeto de entrada.',
'Escolhe componentes aditivos de consumo conhecidos pelo contrato.',
'Soma os dois registros, usando zero quando ausentes. Sem acumular, subagentes/retries poderiam desaparecer do custo.',
'Incrementa contagem de chamadas; default 1 representa uma chamada atual sem contador explícito.',
'Copia atribuições anteriores por agente; evita perder o custo de especialistas.',
'Adiciona atribuição somente quando houve chamada nesta etapa.',
'Obtém o agente da chamada; usa main para chamadas sem nome explícito.',
'Soma componentes de custo e tokens por agente, preservando o histórico.',
'Anexa o mapa de atribuição ao agregado para inspeção e governança.',
'Retorna o agregado que será usado pelo ledger e pela interface.']),
]


CODE_SPECS.append(('sse','Streaming que respeita fragmentos de rede','apps/web-react/src/api.ts','createSSEParser',['http','clientes'],[
'Recebe callback tipado de eventos e devolve uma função de consumo incremental; não envia requisição de rede.',
'O buffer pertence ao closure e sobrevive a vários chunks. Recriá-lo por chunk perderia eventos partidos.',
'Cria a função que recebe cada fragmento de texto já decodificado em UTF-8.',
'Acumula o fragmento sem presumir que ele termina num evento completo.',
'Declara a posição do delimitador, incluindo a possibilidade de não haver evento completo.',
'Procura linha vazia em LF ou CRLF; o loop processa múltiplos eventos que chegam no mesmo chunk.',
'Extrai somente o frame completo anterior ao delimitador.',
'Retira do buffer o frame consumido e conserva a cauda incompleta para o próximo chunk.',
'Define o tipo padrão de evento quando não há campo event.',
'Prepara as linhas de dados, porque um evento SSE pode ter mais de um campo data.',
'Percorre linhas do frame sem confundir cada linha com um evento independente.',
'Extrai o nome do evento e remove espaço exterior. Sem isso, a UI não distinguiria token de status.',
'Reconhece somente linhas data como parte do payload.',
'Remove o prefixo e no máximo um espaço, preservando outros espaços do conteúdo.',
'Encerra processamento de linhas; a emissão acontece só após montar todo o frame.',
'Une dados com quebra de linha, interpreta JSON e chama o consumidor. JSON inválido falha antes de atualizar estado.',
'Volta à busca de outro frame completo; a cauda permanece no buffer.',
'Limita buffer incompleto a 2 MiB para reduzir risco de crescimento sem delimitador.',
'Falha explicitamente quando o limite é excedido; não apresenta um evento truncado como válido.',
'Encerra a função de consumo preservando o closure para a próxima chamada.',
'Encerra a fábrica de parser; cada conexão deve possuir sua própria instância.'
]))

def extract(path,name):
 text=(ROOT/path).read_text()
 if path.endswith('.ts'):
  all_lines=text.splitlines()
  start=next(i for i,line in enumerate(all_lines) if line.startswith(f'export function {name}('))
  end=next(i for i in range(start+1,len(all_lines)) if all_lines[i]=='}')
  return start+1,all_lines[start:end+1],text
 node=next(n for n in ast.walk(ast.parse(text)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
 lines=text.splitlines()[node.lineno-1:node.end_lineno]
 return node.lineno,lines,text

def build():
 DIST.mkdir(exist_ok=True)
 snippets=[]
 for sid,title,path,name,chapters,notes in CODE_SPECS:
  start,lines,source=extract(path,name)
  significant=[(start+i,l) for i,l in enumerate(lines) if l.strip()]
  if len(significant)!=len(notes):
   raise ValueError(f'Line explanation mismatch {sid}: {len(significant)} source lines, {len(notes)} notes. Review changed source.')
  snippets.append(dict(id=sid,title=title,path=path,start=start,end=start+len(lines)-1,code='\n'.join(lines),source_sha256=hashlib.sha256(source.encode()).hexdigest(),snippet_sha256=hashlib.sha256('\n'.join(lines).encode()).hexdigest(),chapters=chapters,explanations=[dict(line=n,text=t) for (n,_),t in zip(significant,notes)]))
 refs=[]
 for c in CHAPTERS:
  for path in c['files']:
   if not (ROOT/path).exists(): raise ValueError(f'Missing code reference: {path} in {c["id"]}')
  refs.extend(c['sources'])
 if set(refs)-set(SOURCES): raise ValueError('Unknown primary source')
 data=dict(chapters=CHAPTERS,sources=SOURCES,glossary=GLOSSARY,snippets=snippets,revision=REV,working_tree=DIRTY,source_check_date='2026-10-20',schema_version=1)
 output=json.dumps(data,ensure_ascii=False,separators=(',',':'))
 (HERE/'data.json').write_text(output)
 for name in ['index.html','styles.css','app.js','math.mjs','favicon.svg','data.json']:
  shutil.copy2(HERE/name,DIST/name)
 (DIST/'.nojekyll').write_text('')
 manifest={name:hashlib.sha256((DIST/name).read_bytes()).hexdigest() for name in ['index.html','styles.css','app.js','math.mjs','favicon.svg','data.json']}
 (DIST/'manifest.json').write_text(json.dumps(dict(files=manifest,chapters=len(CHAPTERS),snippets=len(snippets),revision=REV),indent=2))
 print(f'Built {len(CHAPTERS)} chapters, {len(GLOSSARY)} glossary terms, {len(snippets)} verified snippets to {DIST}')
if __name__=='__main__':build()
