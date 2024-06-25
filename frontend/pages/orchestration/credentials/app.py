from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient
from frontend.st_utils import initialize_st_page, get_backend_api_client
import streamlit as st


initialize_st_page(title="Credentials", icon="🔑")

# Page content
client = get_backend_api_client()
NUM_COLUMNS = 4


@st.cache_data
def get_all_connectors_config_map():
    return client.get_all_connectors_config_map()

# Section to display available accounts and credentials
accounts = client.get_accounts()
all_connector_config_map = get_all_connectors_config_map()
st.header("Available Accounts and Credentials")

if accounts:
    n_accounts = len(accounts)
    accounts.remove("master_account")
    accounts.insert(0, "master_account")
    for i in range(0, n_accounts, NUM_COLUMNS):
        cols = st.columns(NUM_COLUMNS)
        for j, account in enumerate(accounts[i:i + NUM_COLUMNS]):
            with cols[j]:
                st.subheader(f"🏦  {account}")
                credentials = client.get_credentials(account)
                st.json(credentials)
else:
    st.write("No accounts available.")

st.markdown("---")

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    # Section to create a new account
    st.header("Create a New Account")
    new_account_name = st.text_input("New Account Name")
    if st.button("Create Account"):
        new_account_name = new_account_name.replace(" ", "_")
        if new_account_name:
            if new_account_name in accounts:
                st.warning(f"Account {new_account_name} already exists.")
                st.stop()
            elif new_account_name == "":
                st.warning("Please enter a valid account name.")
                st.stop()
            response = client.add_account(new_account_name)
            st.write(response)
        else:
            st.write("Please enter an account name.")

with c2:
    # Section to delete an existing account
    st.header("Delete an Account")
    delete_account_name = st.selectbox("Select Account to Delete", options=accounts if accounts else ["No accounts available"], )
    if st.button("Delete Account"):
        if delete_account_name and delete_account_name != "No accounts available":
            response = client.delete_account(delete_account_name)
            st.warning(response)
        else:
            st.write("Please select a valid account.")

with c3:
    # Section to delete a credential from an existing account
    st.header("Delete Credential")
    delete_account_cred_name = st.selectbox("Select the credentials account", options=accounts if accounts else ["No accounts available"],)
    creds_for_account = [credential.split(".")[0] for credential in client.get_credentials(delete_account_cred_name)]
    delete_cred_name = st.selectbox("Select a Credential to Delete", options=creds_for_account if creds_for_account else ["No credentials available"])
    if st.button("Delete Credential"):
        if (delete_account_cred_name and delete_account_cred_name != "No accounts available") and (delete_cred_name and delete_cred_name != "No credentials available"):
            response = client.delete_credential(delete_account_cred_name, delete_cred_name)
            st.warning(response)
        else:
            st.write("Please select a valid account.")

st.markdown("---")

# Section to add credentials
st.header("Add Credentials")
c1, c2 = st.columns([1, 1])
with c1:
    account_name = st.selectbox("Select Account", options=accounts if accounts else ["No accounts available"])
with c2:
    all_connectors = list(all_connector_config_map.keys())
    binance_perpetual_index = all_connectors.index("binance_perpetual") if "binance_perpetual" in all_connectors else None
    connector_name = st.selectbox("Select Connector", options=all_connectors, index=binance_perpetual_index)
    config_map = all_connector_config_map[connector_name]

st.write(f"Configuration Map for {connector_name}:")
config_inputs = {}
cols = st.columns(NUM_COLUMNS)
for i, config in enumerate(config_map):
    with cols[i % (NUM_COLUMNS - 1)]:
        config_inputs[config] = st.text_input(config, type="password", key=f"{connector_name}_{config}")

with cols[-1]:
    if st.button("Submit Credentials"):
        response = client.add_connector_keys(account_name, connector_name, config_inputs)

