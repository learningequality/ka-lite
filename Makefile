.PHONY: clean-pyc clean-build docs clean

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with pep8"
	@echo "test - run tests the default Python"
	@echo "test-bdd - run BDD tests only"
	@echo "test-nobdd - run non-BDD tests only"
	@echo "assets - build all JS/CSS assets"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release, options: format=[gztar,zip]"
	@echo "dist - package locally, options: format=[gztar,zip]"
	@echo "install - install the package to the active Python's site-packages"

# used for release and dist targets
format?=gztar

clean: clean-build clean-pyc clean-test

clean-dev-db:
	rm -f kalite/database/data.sqlite

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr dist-packages/
	rm -fr dist-packages-temp/
	rm -fr kalite/database/templates
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint:
	pep8 kalite
	jshint kalite/*/static/js/*/

test:
	bin/kalite manage test --bdd-only

test-bdd: docs
	bin/kalite manage test --bdd-only

test-nobdd:
	bin/kalite manage test --no-bdd

test-all:
	@echo "Not supported yet"
	# tox

coverage:
	coverage run --source kalite kalitectl.py test
	coverage report -m

coverage-bdd:
	coverage run --source kalite kalitectl.py test --bdd-only
	coverage report -m

coverage-nobdd:
	coverage run --source kalite kalitectl.py test --no-bdd
	coverage report -m

docs:
	# rm -f docs/ka-lite.rst
	# rm -f docs/modules.rst
	# sphinx-apidoc -o docs/ ka-lite-gtk
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	# open docs/_build/html/index.html


# Runs separately from the docs command for now because of Windows issues
man:
	cli2man bin/kalite -o docs/kalite.1.gz

assets:
	# Necessary because NPM may have wrong versions in the cache
	npm cache clean
	npm install --production
	node build.js
	bin/kalite manage compileymltojson
	bin/kalite manage syncdb --noinput
	bin/kalite manage migrate
	mkdir -p kalite/database/templates/
	cp kalite/database/data.sqlite kalite/database/templates/
	bin/kalite manage retrievecontentpack download en --minimal --foreground --template

release: dist man
	ls -l dist
	echo "uploading above to PyPi, using twine"
	twine upload -s --sign-with gpg2 dist/*

dist: clean clean-dev-db docs assets
	python setup.py sdist --formats=$(format)
	python setup.py sdist --formats=$(format) --static
	ls -l dist

install: clean
	python setup.py install
