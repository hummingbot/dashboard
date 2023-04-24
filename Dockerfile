# Set the base image
FROM continuumio/miniconda3:latest AS builder

# Install system dependencies
RUN apt-get update && \
    apt-get install -y sudo libusb-1.0 python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /home/streamlit-apps

# Create conda environment
COPY environment_conda.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment_conda.yml && \
    conda clean -afy && \
    rm /tmp/environment_conda.yml

# Copy remaining files
COPY main.py .
COPY pages/ pages/
COPY utils/ utils/
COPY CONFIG.py .
COPY .streamlit/ .streamlit/


SHELL [ "/bin/bash", "-lc" ]
RUN echo "conda activate streamlit-apps" >> ~/.bashrc

# Build final image using artifacts from builder
FROM continuumio/miniconda3:latest AS release

# Dockerfile author / maintainer
LABEL maintainer="Fede Cardoso @dardonacci <federico@hummingbot.org>"

# Build arguments
ARG BRANCH=""
ARG COMMIT=""
ARG BUILD_DATE=""
LABEL branch=${BRANCH}
LABEL commit=${COMMIT}
LABEL date=${BUILD_DATE}

# Set ENV variables
ENV COMMIT_SHA=${COMMIT}
ENV COMMIT_BRANCH=${BRANCH}
ENV BUILD_DATE=${DATE}

ENV INSTALLATION_TYPE=docker

# Install system dependencies
RUN apt-get update && \
    apt-get install -y && \
    rm -rf /var/lib/apt/lists/*

# Create mount points
RUN mkdir -p /home/streamlit-apps/data

WORKDIR /home/streamlit-apps

# Copy all build artifacts from builder image
COPY --from=builder /opt/conda/ /opt/conda/
COPY --from=builder /home/ /home/

EXPOSE 8501

# Setting bash as default shell because we have .bashrc with customized PATH (setting SHELL affects RUN, CMD and ENTRYPOINT, but not manual commands e.g. `docker run image COMMAND`!)
SHELL [ "/bin/bash", "-lc" ]

# Set the default command to run when starting the container

CMD conda activate streamlit-apps && streamlit run main.py
