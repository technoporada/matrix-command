.PHONY: run venv install clean test lint help

venv:
	@python3 -m venv .venv
	@echo "✅ Venv created"

install: venv
	@.venv/bin/pip install -r requirements.txt
	@echo "✅ Zależności zainstalowane"

run: install
	@.venv/bin/python app.py

test:
	@.venv/bin/pytest tests/ -v

lint:
	@.venv/bin/ruff check .
	@.venv/bin/black --check .

help:
	@echo "Dostępne cele Make:"
	@echo "  make venv      - Stwórz środowisko wirtualne"
	@echo "  make install   - Zainstaluj zależności"
	@echo "  make run       - Uruchom aplikację"
	@echo "  make test      - Uruchom testy"
	@echo "  make lint      - Sprawdź kod (linting/format)"