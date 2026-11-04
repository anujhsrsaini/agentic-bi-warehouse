.PHONY: install seed test demo mcp clean lint eval

install:
	pip install -e .

seed:
	python3 scripts/seed_dataset.py

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

demo:
	python3 demo.py

mcp:
	python3 -m src.mcp.server

lint:
	ruff check src/ tests/ eval/ scripts/

eval:
	python3 eval/benchmark_runner.py

clean:
	rm -rf .pytest_cache/ .cache/ build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
