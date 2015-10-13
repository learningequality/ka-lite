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
	@echo "release - package and upload a release"
	@echo "dist - package locally"
	@echo "install - install the package to the active Python's site-packages"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr dist-packages/
	rm -fr dist-packages-temp/
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

test-bdd:
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
	cli2man bin/kalite -o docs/kalite.1.gz
	# open docs/_build/html/index.html

assets:
	# Necessary because NPM may have wrong versions in the cache
	npm cache clean
	npm install --production
	node build.js
	bin/kalite manage compileymltojson
	bin/kalite manage init_content_items

release: clean docs assets
	python setup.py sdist --formats=gztar,zip upload --sign
	python setup.py sdist --formats=gztar,zip upload --sign --static
	ls -l dist

dist: clean docs assets
	python setup.py sdist
	python setup.py sdist --static
	ls -l dist

install: clean
	python setup.py install
