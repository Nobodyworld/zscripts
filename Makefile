.PHONY: fmt lint type test security check

fmt:
ruff format .

lint:
ruff check .

type:
mypy .

security:
bandit -q -r zscripts sample_project

test:
pytest

check: fmt lint type security test
