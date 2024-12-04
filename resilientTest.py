import ipfshttpclient
from resdb_driver import Resdb
from resdb_driver.crypto import generate_keypair

# Initialize ResilientDB client
db_root_url = "http://127.0.0.1:18000"
db = Resdb(db_root_url)

# Connect to IPFS
ipfs_client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")


# Function to upload a file to IPFS and return the CID
# just as a note, the IPFS add() function returns three values:
# "Name", "Hash", and "Size"
def upload_to_ipfs(file_path):
    res = ipfs_client.add(file_path)
    file_cid = res["Hash"]
    print(f"File uploaded to IPFS with CID: {file_cid}")
    return file_cid


# FOR REFERENCE: resilientDB transaction structure
# {
#     "id": id,
#     "version": version,
#     "inputs": inputs,
#     "outputs": outputs,
#     "operation": operation,
#     "asset": asset,
#     "metadata": metadata
# }


# Function to create a digital asset in ResilientDB
def create_asset(file_cid, file_name, file_type, owner_public_key, owner_private_key, owner_name):
    asset_metadata = {
        "data": {
            "file_info": {
                "cid": file_cid,
                "file_name": file_name,
                "file_type": file_type,
                "owner_key": owner_public_key,
                "owner_name": owner_name
            },
            "description": f"File '{file_name}' uploaded by {owner_name}",
        },
    }
    

    prepared_tx = db.transactions.prepare(
        operation="CREATE",
        signers=owner_public_key,
        recipients=[([owner_public_key], 1)],
        asset=asset_metadata,
    )
    
    fulfilled_tx = db.transactions.fulfill(prepared_tx, private_keys=owner_private_key)
    db.transactions.send_commit(fulfilled_tx)
    print(f"Asset created and committed with transaction ID: {fulfilled_tx['id']}")
    return fulfilled_tx["id"]

# Function to retrieve asset metadata from ResilientDB
def retrieve_asset(tx_id):
    # Fetch the transaction from ResilientDB
    tx = db.transactions.retrieve(txid=tx_id)
    print(f"Retrieved transaction: {tx}")
    try:
        return tx["asset"]["data"]["file_info"]
    except KeyError as e:
        raise KeyError(f"Error retrieving file_info: {e}. Transaction structure: {tx}")


# function to transfer ownership of the file
# this function lowkey might not be necessary lol
def transfer_ownership(asset_tx_id, new_owner_public_key, new_owner_name, current_owner_private_key):
    try:
        asset = db.transactions.retrieve(txid=asset_tx_id)
        if not asset:
            print(f"Error: Asset with transaction ID {asset_tx_id} not found.")
            return

        # Extract and update the asset metadata
        updated_metadata = asset["asset"]["data"]
        if "file_info" not in updated_metadata:
            print("Error: Invalid asset metadata structure.")
            return

        updated_metadata["file_info"]["owner_key"] = new_owner_public_key
        updated_metadata["file_info"]["owner_name"] = new_owner_name

        # Prepare transfer transaction
        transfer_input = {
            "fulfillment": asset["outputs"][0]["condition"]["details"],
            "fulfills": {"output_index": 0, "transaction_id": asset_tx_id},
            "owners_before": asset["outputs"][0]["public_keys"],
        }

        prepared_transfer_tx = db.transactions.prepare(
            operation="TRANSFER",
            asset={"id": asset_tx_id},  # original asset id
            metadata=updated_metadata,  # Updated metadata
            inputs=transfer_input,
            recipients=[([new_owner_public_key], 1)],  # new owner transfer key
        )

        # Fulfill and commit the transfer transaction
        fulfilled_transfer_tx = db.transactions.fulfill(
            prepared_transfer_tx, private_keys=current_owner_private_key
        )
        db.transactions.send_commit(fulfilled_transfer_tx)

        print(f"Ownership successfully transferred to {new_owner_name} ({new_owner_public_key})")
        print(f"New Transaction ID: {fulfilled_transfer_tx['id']}")
        return fulfilled_transfer_tx["id"]

    except KeyError as e:
        print(f"KeyError: Missing expected field in asset data - {e}")
    except Exception as e:
        print(f"An error occurred during ownership transfer: {e}")


# Retrieving from IPFS instance
def retrieve_from_ipfs(file_cid, save_path):
    try:
        res = ipfs_client.get(file_cid, target=save_path)
        
        print(f"File retrieved from IPFS and saved to: {save_path}")
        return save_path
    
    except Exception as e:
        print(f"Error retrieving file from IPFS: {e}")
        return None


# Example of using the backend functions
if __name__ == "__main__":

    file_path = "/home/echo108471/test.txt"  # Path to the file you want to upload
    file_cid = upload_to_ipfs(file_path)
    

    # Generate key pairs for users
    alice, bob = generate_keypair(), generate_keypair()

    # Create a digital asset in ResilientDB with metadata
    file_name = "test.txt"
    file_type = "txt"
    asset_tx_id = create_asset(file_cid, file_name, file_type, alice.public_key, alice.private_key, "Alice")

    asset_metadata = retrieve_asset(asset_tx_id)
    print(f"Retrieved asset metadata: {asset_metadata}")

    # Transfer ownership of the file to Bob
    transfer_ownership(asset_tx_id, bob.public_key, "Bob", alice.private_key)

    # Retrieve the asset again to confirm the ownership transfer
    updated_asset_metadata = retrieve_asset(asset_tx_id)
    print(f"Updated asset metadata: {updated_asset_metadata}")
    
    file_cid = updated_asset_metadata["cid"]
    save_path = "/home/echo108471/retrieved_files/"
    retrieve_from_ipfs(file_cid, save_path)

