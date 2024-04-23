from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend URL
@app.get("/")
def index():
    return FileResponse("_build/index.html")

@app.exception_handler(404)
async def exception_404_handler(request, exc):
    return FileResponse("_build/index.html")

app.mount("/", StaticFiles(directory="_build/"), name="ui")
