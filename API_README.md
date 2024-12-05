## **Endpoints**

### 1. **Upload and Store File**
Uploads a file to IPFS via Pinata, stores metadata in ResilientDB, and returns the transaction ID.

- **URL:** `/upload_and_store/`
- **Method:** `POST`
- **Request Parameters:**
    - `file`  (form-data `UploadFile`): The file to be uploaded.
    - `owner_name` (form-data `string`): The name of the file owner.
    - `owner_public_key` (form-data `string`): The owner's public key.
    - `owner_private_key` (form-data `string`): The owner's private key.
- **Response:**
    ```json
    {
        "message": "Asset created and committed with transaction ID: <transaction_id>",
        "file_hash": "<transaction_id>",
        "file_metadata": {
            "data": {
                "file_info": { ... },
                "description": "File '<filename>' uploaded by <owner_name>"
            }
        }
    }
    ```

---

### 2. **Retrieve File**
Retrieves a file from IPFS using the transaction ID stored in ResilientDB.

- **URL:** `/retrieve_file/`
- **Method:** `POST`
- **Request Parameters:**
    - `tx_id` (JSON): The transaction ID of the file to be retrieved.
- **Response:**
    - A streaming response containing the requested file.

---

### 3. **Transfer Ownership**
Transfers ownership of an asset to a new owner.

- **URL:** `/transfer_ownership/`
- **Method:** `POST`
- **Request Parameters:**
    - `asset_tx_id` (JSON): The transaction ID of the asset.
    - `new_owner_public_key` (JSON): The public key of the new owner.
    - `new_owner_name` (JSON): The name of the new owner.
    - `current_owner_private_key` (JSON): The private key of the current owner.
- **Response:**
    ```json
    {
        "new_tx_id": "<new_transaction_id>"
    }
    ```

---

## **Error Handling**

### Common Errors:
- **500 Internal Server Error:** Issues with file upload, Pinata integration, or database interaction.
- **404 Not Found:** Metadata or transaction not found in ResilientDB.
- **400 Bad Request:** Invalid request parameters.

### Example Error Response:
```json
{
    "detail": "Error retrieving file metadata: <error_message>"
}
```

## **Notes**
- Validate all cryptographic keys (public/private) to avoid transaction failures.
- Files are temporarily stored on the server and removed after successful processing.
