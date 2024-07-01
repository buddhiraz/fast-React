from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse
from starlette.staticfiles import StaticFiles
import requests
import uvicorn
import pandas as pd
from datetime import datetime
import os
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(
    filename="webhook_events.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the static files from the React build directory
app.mount("/static", StaticFiles(directory="built_react/static"), name="static")

@app.get("/")
def index():
    """
    Serve the React frontend application.

    Returns:
        FileResponse: The index.html file from the React build directory.
    """
    return FileResponse("built_react/index.html")

@app.exception_handler(404)
async def exception_404_handler(request, exc):
    """
    Handle 404 errors by serving the React frontend application.

    Args:
        request (Request): The incoming request.
        exc (Exception): The exception that was raised.

    Returns:
        FileResponse: The index.html file from the React build directory.
    """
    return FileResponse("built_react/index.html")

@app.get("/api/your-endpoint")
async def get_data(org_connection_id: str, request: Request):
    """
    Handle the API call using org_connection_id and save the data to a CSV file.

    Args:
        org_connection_id (str): The organization connection ID.
        request (Request): The incoming request.

    Returns:
        JSONResponse: A response with a success message and the org_connection_id.
    """
    data = {
        "message": "API call successful",
        "org_connection_id": org_connection_id,
    }
    # Save data to CSV
    save_to_csv(request.url._url, org_connection_id)
    return JSONResponse(content=data)

@app.post("/api/authenticate")
async def authenticate(request: Request):
    """
    Authenticate and make an API call to Fasten Connect.

    Args:
        request (Request): The incoming request with the org_connection_id in the body.

    Returns:
        JSONResponse: The response from the Fasten Connect API.
    """
    body = await request.json()
    org_connection_id = body.get("org_connection_id")

    url = "https://api.connect.fastenhealth.com/v1/bridge/fhir/ehi-export"
    payload = { "org_connection_id": org_connection_id }
    headers = {
        "Authorization": "Basic cHVibGljX3Rlc3RfN2Eyc3Zya3pia3l1cjRjNmplMXV3NzU0bmF6M3dneGJoNHplbGJtdTI3aHJrOnByaXZhdGVfdGVzdF9yMig3amh9aVN6NnlqcCYpb3ppciUqVnJNS0Z8P2FCKkl2IVFUZUZHVHpSamE=",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error with Fasten Connect API")
    return JSONResponse(content=response.json())

@app.get("/api/view-csv")
async def view_csv():
    """
    Serve the CSV file containing the organization connection data.

    Returns:
        FileResponse: The CSV file if it exists.
        PlainTextResponse: A 404 response if the CSV file is not found.
    """
    if os.path.exists("org_connection_data.csv"):
        return FileResponse("org_connection_data.csv", media_type='text/csv', filename="org_connection_data.csv")
    else:
        return PlainTextResponse("CSV file not found", status_code=404)

@app.post("/api/webhook")
async def webhook_listener(request: Request):
    """
    Listen for webhook events and log them to a logfile.

    Args:
        request (Request): The incoming request containing the webhook payload.

    Returns:
        JSONResponse: A success response.
    """
    payload = await request.json()
    log_event(payload)
    return JSONResponse({"status": "success"})

@app.get("/api/view-log")
async def view_log():
    """
    Serve the log file containing the webhook event data.

    Returns:
        FileResponse: The log file if it exists.
        PlainTextResponse: A 404 response if the log file is not found.
    """
    log_file_path = "webhook_events.log"
    if os.path.exists(log_file_path):
        return FileResponse(log_file_path, media_type='text/plain', filename="webhook_events.log")
    else:
        return PlainTextResponse("Log file not found", status_code=404)

def save_to_csv(url, org_connection_id):
    """
    Save the URL and org_connection_id to a CSV file.

    Args:
        url (str): The URL containing the org_connection_id.
        org_connection_id (str): The organization connection ID.
    """
    file_path = "org_connection_data.csv"
    data = {
        "timestamp": [datetime.now().isoformat()],
        "url": [url],
        "org_connection_id": [org_connection_id]
    }
    df = pd.DataFrame(data)
    
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, index=False)

def log_event(payload):
    """
    Log the webhook event to a logfile.

    Args:
        payload (dict): The webhook payload.
    """
    event_data = {
        "timestamp": datetime.now().isoformat(),
        "event_id": payload.get("id"),
        "event_type": payload.get("type"),
        "org_connection_id": payload["data"].get("org_connection_id"),
        "download_link": payload["data"].get("download_link")
    }
    logging.info(event_data)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
