import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

# Load application settings
settings = get_settings()

# Create the FastAPI app
app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Social Video RAG Backend is running.",
        "docs": "/docs",
    }
