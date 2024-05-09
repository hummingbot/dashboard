.ONESHELL:
.PHONY: run
.PHONY: conda_remove
.PHONY: conda_create

run:
	streamlit run main.py

uninstall:
	conda env remove -n dashboard

install:
	conda env create -f environment_conda.yml

docker_build:
	docker build -t hummingbot/dashboard:latest .

docker_run:
	docker run -p 8501:8501 dashboard:latest