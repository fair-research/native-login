PYTHON=python
PIP=pip

.PHONY: lint test
lint:
	flake8 --max-complexity=10
test:
	pytest

.PHONY: test
release: clean test
	$(PYTHON) setup.py sdist
	# Make wheel this way to avoid including tests in the resulting package
	$(PIP) wheel --no-index --no-deps --wheel-dir dist dist/*.tar.gz

.PHONY: upload
upload: release
	twine check dist/*
	twine upload dist/*

.PHONY: testupload
testupload: release
	twine check dist/*
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: clean
clean:
	rm -rf dist build *.egg-info