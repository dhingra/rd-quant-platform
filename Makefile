.PHONY: install test lint format typecheck terminal smoke
install:
	python -m pip install -e .[dev,ui]
test:
	pytest
lint:
	ruff check src tests apps
format:
	ruff format src tests apps
typecheck:
	mypy src/rdqp
terminal:
	streamlit run apps/terminal/streamlit_app.py
smoke:
	rdqp --ticks 20
