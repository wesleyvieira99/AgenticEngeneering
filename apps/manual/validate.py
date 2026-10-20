#!/usr/bin/env python3
"""Structural/content/source verification, not a substitute for browser or external-service tests."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
DIST=HERE/'dist'
data=json.loads((DIST/'data.json').read_text())
chapters=data['chapters']
ids={c['id'] for c in chapters}
assert len(ids)==len(chapters)==28, 'Chapter IDs/count'
required=['problem','simple','technical','mechanism','example','math','implementation','files','commands','expected','errors','tradeoffs','impacts','exercise','solution','interview','sources','criterion','prereq']
for c in chapters:
 for key in required:
  assert key in c, f'{c["id"]}: missing {key}'
  assert key=='prereq' or c[key], f'{c["id"]}: empty {key}'
 assert set(c['prereq'])<=ids, f'{c["id"]}: prerequisite missing'
 assert c['id'] not in c['prereq'], 'Self prerequisite'
 assert all((ROOT/f).exists() for f in c['files']), f'{c["id"]}: missing code path'
 assert len(c['mechanism'].split())>=95, f'{c["id"]}: mechanism too thin'
 assert len(c['interview'].split())>=20, f'{c["id"]}: interview answer too thin'
 assert all(s in data['sources'] for s in c['sources']), 'Unknown primary source'
# Prove prerequisite DAG, including forward references such as FinOps before multiagent.
visited=set();active=set()
def visit(id):
 assert id not in active, f'Prerequisite cycle at {id}'
 if id in visited:return
 active.add(id)
 for p in next(c for c in chapters if c['id']==id)['prereq']:visit(p)
 active.remove(id);visited.add(id)
for id in ids:visit(id)
for snippet in data['snippets']:
 source=(ROOT/snippet['path']).read_text()
 expected='\n'.join(source.splitlines()[snippet['start']-1:snippet['end']])
 assert snippet['code']==expected, f'Source drift: {snippet["id"]}'
 assert hashlib.sha256(source.encode()).hexdigest()==snippet['source_sha256'], 'Source hash drift'
 assert hashlib.sha256(expected.encode()).hexdigest()==snippet['snippet_sha256'], 'Snippet hash drift'
 assert len(snippet['explanations'])==len([x for x in expected.splitlines() if x.strip()]), 'Each authored line needs explanation'
 assert set(snippet['chapters'])<=ids
manifest=json.loads((DIST/'manifest.json').read_text())
for name,digest in manifest['files'].items():
 assert hashlib.sha256((DIST/name).read_bytes()).hexdigest()==digest, f'Build hash mismatch: {name}'
html=(DIST/'index.html').read_text()
assert 'lang="pt-BR"' in html and 'id="conteudo"' in html and 'type="module"' in html
for asset in re.findall(r'(?:src|href)="(\./[^"#]+)"',html):
 assert (DIST/asset.removeprefix('./')).exists(), f'Missing local asset {asset}'
js=(DIST/'app.js').read_text()
assert 'history.pushState' not in js, 'Use hash routes on repository Pages'
assert './data.json' in js and './math.mjs' in js
assert 'window.print()' in js and 'navigator.clipboard' in js
assert '@media print' in (DIST/'styles.css').read_text()
assert 'prefers-reduced-motion' in (DIST/'styles.css').read_text()
assert not re.search(r'(https?://[^\s"\']+)\.(?:woff|ttf)',html), 'No external font dependency'
subprocess.run(['node','--check',str(DIST/'app.js')],check=True)
subprocess.run(['node',str(HERE/'math.test.mjs')],check=True)
word_count=sum(len(str(v).split()) for c in chapters for v in c.values())
print(json.dumps({'result':'pass','chapters':len(chapters),'pedagogical_points_per_chapter':19,'authored_words_approx':word_count,'glossary_terms':len(data['glossary']),'source_snippets':len(data['snippets']),'annotated_source_lines':sum(len(s['explanations']) for s in data['snippets']),'checks':['content','prerequisite_dag','code_paths','snippet_hashes','line_annotations','assets','manifest','js_syntax','numerical_properties'],'not_checked':['external URL reachability','browser interactions','production services']},ensure_ascii=False,indent=2))
