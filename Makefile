.PHONY: verify-setup test lint-contract install install-dev run seed users role ekranu-karte lomu-infografika a11y

verify-setup:
	@python --version
	@python -c "import fastapi, pydantic, httpx, pytest, schemathesis; assert pydantic.VERSION.startswith('2'), 'Pydantic v2 required'; print('packages OK')"
	@claude --version
	@test -s setup/claude-answer.md || (echo 'MISSING: setup/claude-answer.md (A0 step 6)'; exit 1)
	@pytest -q tests/test_smoke.py

test:
	pytest -q

lint-contract:
	python tools/lint_contract.py docs/openapi.yaml

install:
	pip install -r requirements.txt

# Piekļūstamības pārbaudei (make a11y) un ekrānu kartei (make ekranu-karte)
install-dev:
	pip install -r requirements-dev.txt
	python -m playwright install chromium

run:
	flask --app app.main:create_app run --host 0.0.0.0 --port 8000 --reload

seed:
	python -m app.seed

users:
	python -m app.roles list

# Lietošana: make role EMAIL=vards@example.com ROLE=darbinieks
role:
	python -m app.roles set "$(EMAIL)" "$(ROLE)"

# Atjauno ekrānu kartes attēlu no docs/ekranu-karte.html (vajag: pip install playwright && playwright install chromium)
ekranu-karte:
	python tools/html_to_png.py docs/ekranu-karte.html docs/ekranu-karte.png

# N1: axe-core + Playwright piekļūstamības pārbaude; rezultāts docs/a11y-rezultati.json (rāda /pieklustamiba)
a11y:
	python tests/a11y_check.py

lomu-infografika:
	python tools/html_to_png.py docs/lomu-pieskirsana.html docs/lomu-pieskirsana.png
