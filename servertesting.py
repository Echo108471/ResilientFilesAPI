import requests
from resdb_driver.crypto import generate_keypair
import os
import json

# generating Keypairs
alice = generate_keypair()
bob = generate_keypair()

url = "https://resilientfilesapi.onrender.com/upload_and_store/"
url1 = "https://resilientfilesapi.onrender.com/retrieve_file/"
url2 = "https://resilientfilesapi.onrender.com/transfer_ownership/"


folder_path = "/home/echo108471/retrieved_files/"
files = {'file': open('/home/echo108471/file_give/test1.txt', 'rb')}
data = {
    "owner_name": "Alice",
    "owner_public_key": alice.public_key,
    "owner_private_key": alice.private_key
}
response = requests.post(url, files=files, data=data)
result = response.json()
print(result)
asset_tx_id = result.get("file_hash")


retrieve_url = f"{url1}?tx_id={asset_tx_id}"

response = requests.post(retrieve_url)

if response.status_code == 200:
    # Save the file to the specified folder
    file_path = os.path.join(folder_path, f"{asset_tx_id}.txt")

    with open(file_path, "wb") as f:
        f.write(response.content)

    print(f"File successfully retrieved and saved as {file_path}")
else:
    print(f"Failed to retrieve file. Status code: {response.status_code}, Error: {response.text}")
    
# 3. Transfer ownership

print("Transferring ownership...")
transfer_payload = {
    "asset_tx_id": asset_tx_id,
    "new_owner_public_key": bob.public_key,
    "new_owner_name": "Bob",
    "current_owner_private_key": alice.private_key
}

transfer_response = requests.post(url2, json=transfer_payload)

if transfer_response.status_code == 200:
    transfer_result = transfer_response.json()
    print(f"Ownership transferred successfully: {transfer_result}")
else:
    print(f"Ownership transfer failed: {transfer_response.status_code}, {transfer_response.text}")