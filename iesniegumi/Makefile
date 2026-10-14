.PHONY: init run test a11y

init:
	python -c "from app import init_db, HERE; init_db(HERE / 'data.db')"

run:
	python app.py

test:
	pytest -q

# Pieejamības tests (axe-core + Playwright) → a11y-report.md, a11y-report.json
a11y:
	python tests/a11y_check.py
