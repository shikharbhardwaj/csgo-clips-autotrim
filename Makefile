.ONESHELL:
SHELL := /bin/bash
SRC = $(wildcard nbs/*.ipynb)
GIT_SHA := $(shell git rev-parse --short=8 HEAD)

all: csgo-clips-autotrim docs

csgo-clips-autotrim: $(SRC)
	nbdev_build_lib
	touch csgo-clips-autotrim

sync:
	nbdev_update_lib

docs_serve: docs
	cd docs && bundle exec jekyll serve

docs: $(SRC)
	nbdev_build_docs
	touch docs

test:
	nbdev_test_nbs

release: pypi conda_release
	nbdev_bump_version

conda_release:
	fastrelease_conda_package

pypi: dist
	twine upload --repository pypi dist/*

dist: clean
	python setup.py sdist bdist_wheel

clean:
	rm -rf dist

sync_lib:
	nbdev_build_lib
	pip install -e .

build-docker-dev:
	docker build -t csgo-clips-autotrim-dev:pytorch -f Dockerfile-dev .

run-docker-dev:
	./utils/docker-start.sh

build-docker:
	nbdev_export
	docker build -t csgo-clips-autotrim:$(GIT_SHA) .