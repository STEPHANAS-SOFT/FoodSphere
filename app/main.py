from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from .shared.database import engine
from . import models
from . import routes as user
from . import routes as vendor
from . import routes as item


models.Base.metadata.create_all(bind=engine)


# Initialize FastAPI app
app = FastAPI(
    title="FoodSphere",
    description="FoodSphere delivery App",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


# CORS settings
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods={"*"},
    allow_headers={"*"},
)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Hospital Management System API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Function to run with python app/main.py
def run():
    """Launch the FastAPI app with Uvicorn (no CLI needed)."""
    uvicorn.run(
        "app.main:app",       
        host="127.0.0.1",      
        port=8000,
        reload=True           
    )

# Automatically run when executed directly
if __name__ == "__main__":
    run()


app.include_router(user.user_router)
app.include_router(vendor.vendor_router)
app.include_router(item.item_router)