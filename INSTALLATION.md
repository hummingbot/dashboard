
This repository is maintained by Hummingbot Foundation as a companion for users of [Hummingbot](https://github.com/hummingbot/hummingbot), the open source framework for building high-frequency crypto trading bots.

Watch this video to understand how it works:
https://www.loom.com/share/72d05bcbaf4048a399e3f9247d756a63

## Requirements

* 8 GB memory or more (On AWS, this is a `t2.large` instance)
* Linux / Debian / MacOS

## Installation

1 - Install dependencies:

* [Docker Engine](https://docs.docker.com/engine/install/ubuntu/)
* [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/):

2 - Clone repo and navigate to the created directory
```bash
git clone https://github.com/hummingbot/dashboard.git
cd dashboard
```

3 - Create `conda` environment and install dependencies
```bash
make env_create
```

4 - Activate the isolated 'conda' environment
```bash
conda activate dashboard
```

5 - Start the dashboard
```bash
streamlit run main.py
```

## Updating

To update the `dashboard` environment for changes to dependencies defined in `environment.yml`, remove the environment and re-create it:
```
make env_remove
make env_create
```

To updated the `dashboard` source for latest version, run:
```
cd dashboard
git pull
```

## Troubleshooting

### Docker permissions

If you get an error like `Permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock`, run this command to enable Docker permissions:
```
sudo chmod 6666 /var/run/docker.sock
```

### Sym-link data directory

To use the [Strategy Performance page](https://github.com/hummingbot/dashboard/wiki/%F0%9F%9A%80-Strategy-Performance), you need to establish a symbolic link to the `data` directory of your running Hummingbot instance:

The `data` directory differs for Docker versus Source installed Hummingbot:
* Docker installed: `/path/to/hummingbot/hummingbot_files/data`
* Source installed: `/path/to/hummingbot/data`

Create a symlink to your Hummingbot `/data` directory
```bash
# replace `/path/to/hummingbotdata` with the actual path
ln -s /path/to/hummingbotdata data

# if you need to remove the symlink
unlink data
```
