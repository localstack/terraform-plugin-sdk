GOFMT_FILES?=$$(find . -name '*.go')

VENV_BIN ?= python3 -m venv
VENV_DIR ?= .venv
PIP_CMD ?= pip3

ifeq ($(OS), Windows_NT)
	VENV_ACTIVATE = $(VENV_DIR)/Scripts/activate
else
	VENV_ACTIVATE = $(VENV_DIR)/bin/activate
endif

VENV_RUN = . $(VENV_ACTIVATE)

$(VENV_ACTIVATE):
	test -d $(VENV_DIR) || $(VENV_BIN) $(VENV_DIR)
	touch $(VENV_ACTIVATE)

venv: $(VENV_ACTIVATE)    ## Create a new (empty) virtual environment

default: test

test: generate
	go test ./...

lint:
	golangci-lint run

generate:
	go generate ./...
	cd tools; go generate ./...

fmt:
	gofmt -s -w -e $(GOFMT_FILES)

# Run this if working on the website locally to run in watch mode.
website:
	$(MAKE) -C website website

# Use this if you have run `website/build-local` to use the locally built image.
website/local:
	$(MAKE) -C website website/local

# Run this to generate a new local Docker image.
website/build-local:
	$(MAKE) -C website website/build-local

patch-install:
	$(VENV_RUN); $(PIP_CMD) install --upgrade -r requirements.txt

patch-create-tags:
	$(VENV_RUN); python create_all_tags.py

.PHONY: default fmt lint generate test website website/local website/build-local
