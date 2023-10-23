import streamlit_authenticator as stauth
import ruamel.yaml as yaml
import os

# enter admin password or use default t3st01
new_password = input("Enter dashboard password >> ") 
new_password = new_password or "t3st01" 

# extract the hash password from the List
hash_password = stauth.Hasher([new_password]).generate()[0] 

# load the YAML file 
yaml_file = "../credentials.yml" 
with open(yaml_file, "r") as file:
    data = yaml.safe_load(file)

# update the admin password on credentials.yml
data["credentials"]["usernames"]["admin"]["password"] = hash_password 

# write the updated data back to the file
with open(yaml_file, "w") as file:
    yaml.dump(data, file, Dumper=yaml.RoundTripDumper)

print("Admin password has been updated! ")
