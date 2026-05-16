SHELL := /bin/bash
.PHONY: help venv install install-dev run run-dev lint format test freeze docker-build compose-up compose-down migrate alembic-rev clean

help:
	@grep -E "^[-a-zA-Z_]+:" Makefile | sed 's/:.*$$//' | sort | awk '{printf "- %s\n", $$0}'

venv:
	python3 -m venv .venv

install: venv
	. .venv/bin/activate && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

install-dev: venv
	. .venv/bin/activate && pip install --upgrade pip setuptools wheel && \
	if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

run:
	. .venv/bin/activate && python main.py

run-dev:
	FLASK_ENV=development . .venv/bin/activate && python -u main.py

lint:
	. .venv/bin/activate && if command -v flake8 >/dev/null 2>&1; then flake8 .; else echo "flake8 not installed (run make install-dev)"; fi

format:
	. .venv/bin/activate && if command -v black >/dev/null 2>&1; then black .; else echo "black not installed (run make install-dev)"; fi

test:
	. .venv/bin/activate && if command -v pytest >/dev/null 2>&1; then pytest -q; else echo "pytest not installed (run make install-dev)"; fi

freeze:
	. .venv/bin/activate && pip freeze > requirements.txt

docker-build:
	docker build -t cognitive-dialogue:latest .

compose-up:
	docker-compose up --build

compose-down:
	docker-compose down

migrate:
	. .venv/bin/activate && alembic upgrade head

alembic-rev:
	. .venv/bin/activate && alembic revision --autogenerate -m "$(m)"

clean:
	-find . -type f -name '*.pyc' -delete || true
	-rm -rf .venv build dist __pycache__ || true
