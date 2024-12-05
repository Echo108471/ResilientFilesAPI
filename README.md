# Resilient Files API

This project integrates ResilientDB and IPFS to provide an API for managing file storage and metadata. It extends ResilientDB's functionality to support saving JSON "asset" files and additional file types.

The backend is built using FastAPI, and integrates with a Pinata IPFS node and ResilientDB via the Python SDK.

## **Live Backend**
- **Hosted Link**: [Resilient Files API](https://resilientfilesapi.onrender.com)
- Visit `/docs` to view all available API endpoints.
- **Endpoints Overview**: A detailed list of available endpoints can be found [here.](https://github.com/Echo108471/ResilientFilesAPI/blob/main/API_README.md)

**Note**: Avoid uploading large files bc I have pinata free tier lmao

---

## **Project Structure**
- `main_server.py`: The main FastAPI server file.
- `main_server_local.py`: The local version of the FastAPI server file.
- `servertesting.py`: A Python script for testing server functionality.
- `resilientTest.py`: A test script for validating ResilientDB integration.
- `requirements.txt`: Lists all Python dependencies for the project.

---

## **Setup Instructions (Local Installation on Ubuntu 20.04)**

### **1. Configure Local Paths**
To run the project on custom IPFS Pinata nodes and/or a personal hosted ResilientDB instance:
1. Edit `main_server_local.py` to set:
   - `db_root_url` (ResilientDB URL)
2. Modify endpoints as necessary for alternative IPFS configurations.
3. If not using a custom setup, skip this step.

---

### **2. Setting Up ResilientDB**
 - Assuming you have already setup ResilientDB before
 - If not, please refer [here](https://github.com/apache/incubator-resilientdb)

#### **Terminal 1: Start Key-Value Service**
1. Navigate to the ResilientDB directory:
   ```bash
   cd service/tools/kv
   ```
2. Start the Key-Value service:
   ```bash
   ./start_kv_service.sh
   ```

#### **Terminal 2: Start GraphQL API**
1. Build the GraphQL service (first-time setup only):
   ```bash
   bazel build service/http_server:crow_service_main
   ```
2. Run the GraphQL API:
   ```bash
   bazel-bin/service/http_server/crow_service_main service/tools/config/interface/client.config service/http_server/server_config.config
   ```

#### **Terminal 3: Start IPFS Daemon**

1. Download the IPFS binary:
   ```bash
   wget https://dist.ipfs.tech/go-ipfs/v0.7.0/go-ipfs_v0.7.0_linux-amd64.tar.gz
   ```

2. Extract and install IPFS:
   ```bash
   tar -xvzf go-ipfs_v0.7.0_linux-amd64.tar.gz
   cd go-ipfs
   sudo mv ipfs /usr/local/bin/
   ```

3. Verify the installation:
   ```bash
   ipfs --version
   ```
   You should see `ipfs version 0.7.0`.

4. If running IPFS for the first time, initialize it:
   ```bash
   ipfs init
   ```
   
5. Start the IPFS daemon:
   ```bash
   ipfs daemon
   ```

---

### **3. Running the Application**
#### **1. Activate the Virtual Environment**
```bash
source venv/bin/activate
```

#### **2. Install Dependencies**
Ensure all Python dependencies are installed:
```bash
pip install -r requirements.txt
```

#### **3. Start the FastAPI Server**
Run the following command to start the FastAPI server:
```bash
uvicorn main_server_local:app --reload
```

---

## **Troubleshooting**

- **IPFS Connection Issues**: Ensure the IPFS daemon is running (`ipfs daemon`) and accessible at `localhost:5001`.
- **ResilientDB Errors**: Confirm the Key-Value service and GraphQL API are active and configured correctly.
- **Environment Issues**: Use a virtual environment to isolate dependencies:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

---

## **Notes**
1. The `ipfs-go` and `ipfshttpclient` versions **must match** (e.g., `v0.7.0`).
2. Ensure all services (ResilientDB Key-Value, GraphQL API, and IPFS daemon) are running before launching the application.

---
