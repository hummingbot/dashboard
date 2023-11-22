import streamlit_authenticator as stauth
from ruamel.yaml import YAML
import os

yaml = YAML(typ='safe', pure=True)

# enter email address
new_email = input("Enter dashboard email >> ") 

# if user enter no email address, exit setup!
if len(new_email) == 0:
    print("\nNo email added, please try again!\n")
    exit()

# load the YAML file 
yaml_file = "../credentials.yml" 
with open(yaml_file, "r") as file:
    data = yaml.load(file)

# append the email address to credentials.yml
data["preauthorized"]["emails"].append(new_email)

# write the updated data back to the file
with open(yaml_file, "w") as file:
    yaml.dump(data, file)

print("Email has been successfully added!")
