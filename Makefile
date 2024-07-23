.ONESHELL:
.SHELLFLAGS := -c

.PHONY: run
.PHONY: uninstall
.PHONY: install
.PHONY: install-pre-commit
.PHONY: docker_build
.PHONY: docker_run


detect_conda_bin := $(shell bash -c 'if [ "${CONDA_EXE} " == " " ]; then \
    CONDA_EXE=$$((find /opt/conda/bin/conda || find ~/anaconda3/bin/conda || \
    find /usr/local/anaconda3/bin/conda || find ~/miniconda3/bin/conda || \
    find /root/miniconda/bin/conda || find ~/Anaconda3/Scripts/conda || \
    find $$CONDA/bin/conda) 2>/dev/null); fi; \
    if [ "${CONDA_EXE}_" == "_" ]; then \
    echo "Please install Anaconda w/ Python 3.10+ first"; \
    echo "See: https://www.anaconda.com/distribution/"; \
    exit 1; fi; \
    echo $$(dirname $${CONDA_EXE})')

CONDA_BIN := $(detect_conda_bin)

run:
	streamlit run main.py --server.headless true

uninstall:
	conda env remove -n dashboard

install:
	if conda env list | grep -q '^dashboard '; then \
	    echo "Environment already exists."; \
	else \
	    conda env create -f environment_conda.yml; \
	fi
	$(MAKE) install-pre-commit

install-pre-commit:
	/bin/bash -c 'source "${CONDA_BIN}/activate" dashboard && \
	if ! conda list pre-commit | grep pre-commit &> /dev/null; then \
	    pip install pre-commit; \
	fi && pre-commit install'

docker_build:
	docker build -t hummingbot/dashboard:latest .

docker_run:
	docker run -p 8501:8501 hummingbot/dashboard:latest
