PYTHON ?= python3.12
PY := .venv/bin/python
COMPOSE := docker compose -f infra/local/compose.yml
.PHONY: setup dev stop api worker seed test test-integration test-e2e evaluate docs-build manual-dev clients-build verify labs infra-validate
setup:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install -r requirements.lock
	.venv/bin/pip install --no-deps -e .
	npm ci --prefix apps/web-react
	npm ci --prefix apps/web-angular
	npm ci --prefix tests/e2e
	npm --prefix tests/e2e exec -- playwright install chromium

dev:
	$(COMPOSE) up --build --wait -d
stop:
	$(COMPOSE) down
api:
	.venv/bin/uvicorn services.api.main:app --host 127.0.0.1 --port 8000
worker:
	$(PY) -m services.worker.main
seed:
	$(PY) scripts/seed.py
test:
	$(PY) -m pytest -q -m 'not integration'
	npm test --prefix apps/web-react
	npm test --prefix apps/web-angular
	node --test apps/manual/math.test.mjs
test-integration:
	$(PY) -m pytest -q -m integration
test-e2e:
	$(PY) scripts/e2e.py
evaluate:
	$(PY) scripts/evaluate.py
docs-build:
	$(PY) apps/manual/build.py
	$(PY) apps/manual/validate.py
manual-dev: docs-build
	$(PY) -m http.server 4173 --bind 127.0.0.1 --directory apps/manual/dist
clients-build:
	npm run build --prefix apps/web-react
	npm run build --prefix apps/web-angular
verify: test evaluate docs-build clients-build
	$(PY) scripts/verify.py
labs:
	$(PY) labs/foundations/main.py
infra-validate:
	terraform -chdir=infra/aws init -backend=false -input=false
	terraform -chdir=infra/aws validate
