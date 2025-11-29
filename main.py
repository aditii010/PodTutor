# backend/app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.routes import episodes

app = FastAPI(title="PodTutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # in prod, restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount storage/ as /static (audio + pdfs)
STATIC_DIR = os.path.join("storage")

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

app.include_router(episodes.router, prefix="/api/episodes", tags=["episodes"])

@app.get("/health")
def health():
    return {"status": "ok"}
