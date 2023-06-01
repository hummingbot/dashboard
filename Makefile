.ONESHELL:
.PHONY: run
.PHONY: conda_remove
.PHONY: conda_create

run:
	streamlit run main.py

env_remove:
	conda env remove -n dashboard

env_create:
	conda env create -f environment_conda.yml

docker_build:
	docker build -t dashboard:latest .

docker_run:
	docker run -p 8501:8501 dashboard:latest