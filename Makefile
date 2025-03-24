pre: format check pre-commit #mypy

format:
	poetry run isort src/
	poetry run isort tests/
	poetry run ruff format src/
	poetry run ruff format tests/


check:
	poetry run isort src/ --check
	poetry run isort tests/ --check
	poetry run ruff check src/
	poetry run ruff check tests/

pre-commit:
	#poetry run pre-commit run --all-files
	poetry run pre-commit run -a --show-diff-on-failure --color always

mypy:
	poetry run mypy src/

deptry:
    # вернёт неиспользуемые зависимости
	poetry run deptry .

tests: tests_python

tests_python:
	# poetry run pytest --cov-report xml --cov src -n 4 tests
	# poetry run pytest --cov-report term --cov-report xml --cov src tests -m "not local"
	poetry run pytest --cov-report term --cov-report xml --cov src tests

# пример использования:
# make migration message="add_rb_id" id="013"
migration:
	alembic revision --autogenerate -m "$(message)" --rev-id "$(id)"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1

start:
	docker compose up --verbose

stop:
	docker compose stop
