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

clean: clean-build clean-pyc clean-test clean-assets

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -rf .kalite_dist_tmp
	rm -fr .eggs/
	rm -fr .pip-temp/
	rm -fr kalite/database/templates
	rm -fr kalite/static-libraries/docs
	find kalite/packages/dist/* -maxdepth 0 -type d -exec rm -fr {} +
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

clean-assets:
	npm cache clean
	rm -rf kalite/database/templates/
	rm -rf .kalite_dist_tmp

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
	coverage run --source kalite bin/kalite test
	coverage report -m


docs:
	# rm -f docs/ka-lite.rst
	# rm -f docs/modules.rst
	# sphinx-apidoc -o docs/ ka-lite-gtk
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	cp -Rf docs/_build/html kalite/static-libraries/docs/
	# open docs/_build/html/index.html


# Runs separately from the docs command for now because of Windows issues
man:
	cli2man bin/kalite -o docs/kalite.1.gz

assets:
	npm install --production
	node build.js
	KALITE_HOME=.kalite_dist_tmp bin/kalite manage syncdb --noinput
	KALITE_HOME=.kalite_dist_tmp bin/kalite manage migrate
	rm -rf kalite/database/templates/
	mkdir -p kalite/database/templates/
	cp .kalite_dist_tmp/database/data.sqlite kalite/database/templates/
	bin/kalite manage retrievecontentpack empty en --foreground --template

release: dist man
	ls -l dist
	echo "Uploading dist/* to PyPi, using twine"
	twine upload -s --sign-with gpg2 dist/*

sdist: clean docs assets
	# Building assets currently creates pyc files in the source dirs,
	# so we should delete those...
	make clean-pyc
	python setup.py sdist --formats=$(format) --static
	python setup.py sdist --formats=$(format)

dist: clean docs assets 
	# Building assets currently creates pyc files in the source dirs,
	# so we should delete those...
	make clean-pyc
	python setup.py sdist --formats=$(format)
	python setup.py bdist_wheel
	python setup.py sdist --formats=$(format) --static
	python setup.py bdist_wheel --static  --no-clean
	ls -l dist

install: clean
	python setup.py install

pex:
	ls dist/ka_lite-*.whl | while read whlfile; do pex $$whlfile -o dist/kalite-`unzip -p $$whlfile kalite/VERSION`.pex -m kalite --python-shebang=/usr/bin/python; done

dockerenvclean:
	docker container prune -f
	docker image prune -f

dockerenvbuild:
	docker image build -t learningequality/kalite:$$(kalite --version) .

dockerenvdist:
	docker run -v $$PWD/dist:/kalitedist learningequality/kalite:$$(kalite --version)
