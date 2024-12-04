import os
import time
import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from resdb_driver import Resdb
from resdb_driver.crypto import generate_keypair
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from io import BytesIO
from tempfile import NamedTemporaryFile
import shutil
import ipfshttpclient

app = FastAPI()

# CORS setup
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ResilientDB setup
db = Resdb("http://127.0.0.1:18000")  # Local ResilientDB
ipfs_client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")  # Local IPFS node

# Models for API
class TransferRequest(BaseModel):
    asset_tx_id: str
    new_owner_public_key: str
    new_owner_name: str
    current_owner_private_key: str


# Endpoint to upload the file and store metadata
@app.post("/upload_and_store/")
async def upload_and_store(
    file: UploadFile = File(...),
    owner_name: str = Form(...),
    owner_public_key: str = Form(...),
    owner_private_key: str = Form(...),
):
    try:
        # Save the uploaded file temporarily
        temp_file_path = file.filename
        async with aiofiles.open(temp_file_path, 'wb') as f:
            while contents := await file.read(1024 * 1024):
                await f.write(contents)

        # Extract file metadata
        file_extension = os.path.splitext(temp_file_path)[1].lstrip(".")
        file_type = file_extension or "unknown"
        file_metadata = {
            "file_name": os.path.basename(temp_file_path),
            "file_size": os.path.getsize(temp_file_path),
            "file_type": file_type,
            "creation_time": time.ctime(os.path.getctime(temp_file_path)),
            "modification_time": time.ctime(os.path.getmtime(temp_file_path)),
            "is_file": os.path.isfile(temp_file_path),
        }

        # Upload file to local IPFS node
        ipfs_res = ipfs_client.add(temp_file_path)
        file_cid = ipfs_res["Hash"]

        # Create digital asset metadata for ResilientDB
        asset_metadata = {
            "data": {
                "file_info": {
                    "cid": file_cid,
                    "file_name": file_metadata["file_name"],
                    "file_type": file_metadata["file_type"],
                    "creation_time": file_metadata["creation_time"],
                    "modification_time": file_metadata["modification_time"],
                    "owner_key": owner_public_key,
                    "owner_name": owner_name,
                },
                "description": f"File '{file_metadata['file_name']}' uploaded by {owner_name}",
            },
        }

        # Clean up the temporary file
        os.remove(temp_file_path)

        # Create a transaction in ResilientDB
        prepared_tx = db.transactions.prepare(
            operation="CREATE",
            signers=owner_public_key,
            recipients=[([owner_public_key], 1)],
            asset=asset_metadata,
        )

        # Fulfill and send the transaction to ResilientDB
        fulfilled_tx = db.transactions.fulfill(prepared_tx, private_keys=owner_private_key)
        db.transactions.send_commit(fulfilled_tx)

        return {
            "message": f"Asset created and committed with transaction ID: {fulfilled_tx['id']}",
            "file_hash": fulfilled_tx["id"],
            "file_metadata": asset_metadata,
        }

    except Exception as e:
        # Handle errors and clean up temp files in case of failure
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing the file: {e}")


# Endpoint to retrieve file from IPFS using ResilientDB transaction hash
@app.post("/retrieve_file/")
def retrieve_file(tx_id: str):
    try:
        # Retrieve metadata from ResilientDB
        tx = db.transactions.retrieve(txid=tx_id)
        updated_asset_metadata = tx["asset"]["data"]["file_info"]
        file_cid = updated_asset_metadata["cid"]

        # Fetch the file from local IPFS
        temp_file = NamedTemporaryFile(delete=False)
        ipfs_client.get(file_cid, target=temp_file.name)

        # Stream the file as response
        temp_file.close()
        with open(temp_file.name, "rb") as f:
            return StreamingResponse(
                BytesIO(f.read()),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={updated_asset_metadata['file_name']}"},
            )

    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Error retrieving file metadata: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file from IPFS: {e}")
    finally:
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            os.remove(temp_file.name)


# Endpoint to transfer ownership of the asset
@app.post("/transfer_ownership/")
def transfer_ownership(request: TransferRequest):
    try:
        # Retrieve the existing asset
        asset = db.transactions.retrieve(txid=request.asset_tx_id)
        if not asset:
            raise ValueError(f"Asset with transaction ID {request.asset_tx_id} not found.")

        # Extract and update the asset metadata
        updated_metadata = asset["asset"]["data"]
        if "file_info" not in updated_metadata:
            raise ValueError("Invalid asset metadata structure. 'file_info' is missing.")

        updated_metadata["file_info"]["owner_key"] = request.new_owner_public_key
        updated_metadata["file_info"]["owner_name"] = request.new_owner_name

        # Prepare transfer transaction
        transfer_input = {
            "fulfillment": asset["outputs"][0]["condition"]["details"],
            "fulfills": {"output_index": 0, "transaction_id": request.asset_tx_id},
            "owners_before": asset["outputs"][0]["public_keys"],
        }

        prepared_transfer_tx = db.transactions.prepare(
            operation="TRANSFER",
            asset={"id": request.asset_tx_id},
            metadata=updated_metadata,
            inputs=transfer_input,
            recipients=[([request.new_owner_public_key], 1)],
        )

        # Fulfill and commit the transfer transaction
        fulfilled_transfer_tx = db.transactions.fulfill(
            prepared_transfer_tx, private_keys=request.current_owner_private_key
        )
        db.transactions.send_commit(fulfilled_transfer_tx)

        return {"new_tx_id": fulfilled_transfer_tx["id"]}

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"KeyError: Missing expected field in asset data - {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during ownership transfer: {e}")
