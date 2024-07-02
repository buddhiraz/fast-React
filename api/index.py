from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse, PlainTextResponse, Response
from starlette.staticfiles import StaticFiles
import pandas as pd
import os
import logging
from datetime import datetime
import requests
import uvicorn

app = FastAPI()

# Configure logging to use an in-memory log
LOG_FILE_PATH = "/tmp/webhook_events.log"

# Ensure the log file exists
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'w') as log_file:
        log_file.write("timestamp,event_id,event_type,org_connection_id,download_link\n")

# Add logging configuration
logging.basicConfig(
    filename=LOG_FILE_PATH,
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

@app.get("/api/view-log")
def view_log():
    """
    View the content of the log file.

    Returns:
        Response: The content of the log file.
    """
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r') as log_file:
            log_content = log_file.read()
        return Response(content=log_content, media_type="text/plain")
    else:
        return Response(content="Log file not found.", media_type="text/plain")

@app.get("/api/download-log")
def download_log():
    """
    Download the log file.

    Returns:
        Response: The log file as an attachment.
    """
    if os.path.exists(LOG_FILE_PATH):
        return Response(
            content=open(LOG_FILE_PATH, 'rb').read(),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="webhook_events.log"'
            }
        )
    else:
        return Response(content="Log file not found.", media_type="text/plain")

def save_to_csv(file_path, data):
    """
    Save the data to a CSV file.

    Args:
        file_path (str): The file path to save the CSV data.
        data (dict): The data to save in the CSV file.
    """
    df = pd.DataFrame(data)
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, index=False)

@app.post("/api/webhook")
async def webhook_listener(request: Request):
    """
    Listen for webhook events and log them to an in-memory log and CSV file.

    Args:
        request (Request): The incoming request containing the webhook payload.

    Returns:
        JSONResponse: A success response.
    """
    payload = await request.json()
    url = payload.get("data", {}).get("download_link")
    org_connection_id = payload.get("data", {}).get("org_connection_id")

    # Log the event
    event_data = {
        "timestamp": datetime.now().isoformat(),
        "event_id": payload.get("id"),
        "event_type": payload.get("type"),
        "org_connection_id": org_connection_id,
        "download_link": url
    }
    logging.info(event_data)

    # Save to CSV
    webhook_csv_path = "/tmp/webhook_events.csv"
    save_to_csv(webhook_csv_path, [event_data])

    return {"status": "success"}

@app.get("/api/view-webhook-csv")
async def view_webhook_csv():
    """
    Serve the CSV file containing the webhook event data.

    Returns:
        FileResponse: The CSV file if it exists.
        PlainTextResponse: A 404 response if the CSV file is not found.
    """
    webhook_csv_path = "/tmp/webhook_events.csv"
    if os.path.exists(webhook_csv_path):
        return FileResponse(webhook_csv_path, media_type='text/csv', filename="webhook_events.csv")
    else:
        return PlainTextResponse("CSV file not found", status_code=404)

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
        "timestamp": [datetime.now().isoformat()],
        "url": [request.url._url],
        "org_connection_id": [org_connection_id]
    }
    # Save data to CSV
    csv_path = "/tmp/org_connection_data.csv"
    save_to_csv(csv_path, data)
    return JSONResponse(content={"message": "API call successful", "org_connection_id": org_connection_id})

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
    payload = {"org_connection_id": org_connection_id}
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
    csv_path = "/tmp/org_connection_data.csv"
    if os.path.exists(csv_path):
        return FileResponse(csv_path, media_type='text/csv', filename="org_connection_data.csv")
    else:
        return PlainTextResponse("CSV file not found", status_code=404)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
