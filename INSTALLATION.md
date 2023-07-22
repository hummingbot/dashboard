## Requirements

You will need to install [StreamLit](https://streamlit.io/). For information about Streamlit installation, see the instructions located at https://docs.streamlit.io/library/get-started/installation.

You will also need to install either [Anaconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) to get Conda:
* [Anaconda](https://www.anaconda.com/) is a comprehensive Python distribution that includes a large number of pre-installed data science libraries and packages. It is designed to be an all-in-one solution for data science and machine learning tasks. When you install Anaconda, it comes with a collection of popular Python packages like NumPy, pandas, matplotlib, scikit-learn, and more. 
* [Miniconda](https://docs.conda.io/en/latest/miniconda.html) is a minimal version of Anaconda. It includes only the essential components, such as Python interpreter and Conda package manager. Unlike Anaconda, Miniconda doesn't come with pre-installed packages, which makes its download size much smaller. 

This repository is maintained by Hummingbot Foundation as a companion for users of [Hummingbot](https://github.com/hummingbot/hummingbot), the open source framework for building high-frequency crypto trading bots.

Watch this video to understand how it works:
https://www.loom.com/share/72d05bcbaf4048a399e3f9247d756a63

## Installation

1. Install Steamlit and Conda packages utilizing their instructions for your specific environment:
* Install  [StreamLit](https://docs.streamlit.io/library/get-started/installation)
* Install [Anaconda](https://docs.anaconda.com/free/anaconda/install/index.html) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

2. Clone this repo and navigate to the created directory
```bash
git clone https://github.com/hummingbot/dashboard.git
cd dashboard
```

3. Run conda command to create an isolated `conda` environment and install dependencies
```
conda env create -f environment_conda.yml
```

4. Activate the isoldated 'conda' environment
```bash
conda activate dashboard
```

5. Run the app
```bash
streamlit run main.py
```

## Data Feed

Your `dashboard` environment needs to have access to the database for your Hummingbot environment. This is done by setting up a symbolic link to the 'data' directory of your running Hummingbot instance. 

The data directory differs for Docker versus Source installed Hummingbot. Data directory for each is as follows:
* Docker installed: /path/to/hummingbot/hummingbot_files/data
* Source installed: /path/to/hummingbot/data


Create a symlink to your Hummingbot `/data` directory
```bash
# replace `/path/to/hummingbotdata` with the actual path
ln -s /path/to/hummingbotdata data

# if you need to remove the symlink
unlink data
```

## Updating Dependencies

To update the `dashboard` environment for new dependencies, run:
```
conda env update -f environment_conda.yml
```

To updated the `dashboard` source for latest version, run:
```
cd dashboard
git pull
```
