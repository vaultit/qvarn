.PHONY: all
all: env env3

.PHONY: env env3
env: env/.done
env3: env3/.done

env/bin/python:
	virtualenv -p python2 env
	env/bin/pip install --upgrade pip wheel setuptools

env3/bin/python:
	virtualenv -p python3 env3
	env3/bin/pip install --upgrade pip wheel setuptools

env/.done: env/bin/python setup.py requirements-dev.txt
	env/bin/pip install -r requirements-dev.txt -f vendor
	env/bin/pip install -e .
	touch env/.done

env3/.done: env3/bin/python setup.py requirements-dev-py3.txt
	env3/bin/pip install -r requirements-dev-py3.txt -f vendor
	env3/bin/pip install -e .
	touch env3/.done

env/bin/pip-compile: env/bin/python
	env/bin/pip install pip-tools

env3/bin/pip-compile: env3/bin/python
	env3/bin/pip install pip-tools

.PHONY: dist
dist: env
	env/bin/python setup.py sdist bdist_wheel

.PHONY: requirements
requirements: env/bin/pip-compile env3/bin/pip-compile
	env/bin/pip-compile requirements.in -o requirements.txt -f vendor
	env/bin/pip-compile requirements.in requirements-dev.in -o requirements-dev.txt -f vendor
	env3/bin/pip-compile requirements.in requirements-dev.in -o requirements-dev-py3.txt -f vendor

.PHONY: upgrade-requirements
upgrade-requirements: env/bin/pip-compile env3/bin/pip-compile
	env/bin/pip-compile --upgrade --no-index requirements.in -o requirements.txt
	env/bin/pip-compile --upgrade --no-index requirements.in requirements-dev.in -o requirements-dev.txt
	env3/bin/pip-compile --upgrade --no-index requirements.in requirements-dev.in -o requirements-dev-py3.txt

.PHONY: test
test: env env3
	./check
	./check py3

.PHONY: test-postgres
test-postgres: env
	./run-yarn-tests -o database.type=postgres

.PHONY: test-sqlite
test-sqlite: env
	./run-yarn-tests -o database.type=sqlite

.PHONY: test-postgres-py3
test-postgres-py3: env env3
	./run-yarn-tests -o database.type=postgres --qvarn-venv=env3

.PHONY: test-sqlite-py3
test-sqlite-py3: env env3
	./run-yarn-tests -o database.type=sqlite --qvarn-venv=env3

.PHONY: test-postgres-all
test-postgres-all: test-postgres test-postgres-py3

.PHONY: test-sqlite-all
test-sqlite-all: test-sqlite test-sqlite-py3
