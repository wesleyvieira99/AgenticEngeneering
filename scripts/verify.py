"""Repository checks: actual local paths, pinned dependencies, no obvious secret files."""
import ast
import csv
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    errors=[]
    for path in ['README.md','CHECKPOINT.md','docs/coverage.csv','docs/verification.md','docs/versions.md','.env.example','apps/manual/dist/index.html','apps/web-react/dist/index.html','apps/web-angular/dist/browser/index.html']:
        if not (ROOT/path).exists():errors.append('Missing '+path)
    coverage=ROOT/'docs/coverage.csv'
    if coverage.exists():
        for row in csv.DictReader(coverage.open()):
            for field in ['code','lab','test','evidence']:
                for reference in row.get(field,'').split(';'):
                    if reference and not (ROOT/reference).exists():errors.append(f'{row["subject"]}: missing {reference}')
            if row['status'] not in ['planejado','implementado','testado localmente','validado com serviço real','documentado','bloqueado']:
                errors.append('Invalid state '+row['status'])
    for path in [ROOT/'apps/web-react/package.json',ROOT/'apps/web-angular/package.json',ROOT/'tests/e2e/package.json']:
        doc=json.loads(path.read_text())
        for name,version in {**doc.get('dependencies',{}),**doc.get('devDependencies',{})}.items():
            if version[:1] in '^~*':errors.append(f'Unpinned: {name}')
    tracked=subprocess.run(['git','ls-files'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    for path in tracked:
        parts=Path(path).parts
        if 'node_modules' in parts or '.venv' in parts or path.endswith('.db') or Path(path).name=='.env':errors.append('Forbidden tracked artifact '+path)
    print(json.dumps({'status':'failed' if errors else 'passed','checks':['deliverables','coverage paths','allowed states','direct dependency pins','tracked artifact hygiene'],'errors':errors},indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
