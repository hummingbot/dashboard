
This repository is maintained by Hummingbot Foundation as a companion for users of [Hummingbot](https://github.com/hummingbot/hummingbot), the open source framework for building high-frequency crypto trading bots.

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
## Configure Credentials for Authentication

### Method 1: Using hasher_generate

1 - Update the Environment
  
    Ensure that you have the latest version of the project and reinstall the conda environment if needed.
  
2 - Generate Hashed Password
  
    Open a Python terminal and utilize hasher_generate from Streamlit to generate a hashed password. Example code:

    ```
    import streamlit_authenticator as st_auth
    hashed_password = st_auth.hasher_generate("YOUR_PLAIN_TEXT_PASSWORD")

    ```

3 - Edit the Credentials YAML File

    Locate the credentials YAML file in the root directory.
    Edit the file by inserting the generated hashed password from Step 2.

4 - Accessing the Dashboard
    
    Run the Hummingbot Dashboard project.
    Use the username and the plain text password (used in Step 2) to log in to the dashboard.

5 - Logging Out
    
    To log out, navigate to the dashboard and select 'Logout'.
    

### Method 2: Using Pre-Authorized Emails for User Registration

1 - Update the Environment

    As in Method 1, ensure your conda environment and project version are up-to-date.

2 - Whitelist Emails

    In the credentials YAML file, add the emails of users who will be pre-authorized to register and create their credentials.

    ```
    pre_authorized_emails:
      - user1@example.com
      - user2@example.com
    ```

3 - User Registration

    Direct users to the Hummingbot Dashboard.
    Users should select 'Register' and enter one of the pre-authorized email addresses.
    They will choose their own username and password during registration.
    
4 - First-Time Login
    
    Users log in with their chosen username and password.
    The dashboard will hash and store their credentials automatically.

5 - Logging Out
    
    Similar to Method 1, users can log out by navigating to the dashboard and selecting 'Logout'.

### Additional Notes

- Video instruction link - https://drive.google.com/file/d/17ecd2aWHZCyuK5Etcv8AZwXMw2B-1sJG/view?usp=share_link
- Users created through Method 2 (Pre-Authorized Emails) will have their hashed passwords automatically generated and stored.
- Always ensure the secure handling and storage of credentials.
- Utilize the 'Logout' feature to secure information and restrict access to the dashboard when it is not in use.

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
