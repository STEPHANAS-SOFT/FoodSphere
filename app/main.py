from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from sqlalchemy.orm import configure_mappers
from .shared.database import engine
from . import models
from . import routes
from .routes import (
    item_category_router, delivery_address_router, rider_router,
    item_addon_group_router, item_addon_router, item_variation_router,
    order_router, cart_router, wallet_router
)
from .routes.order_item_routes import router as order_item_router
from .routes.order_item_addon_routes import router as order_item_addon_router
from .routes.order_tracking_routes import router as order_tracking_router
from .routes.cart_item_routes import router as cart_item_router
from .routes.cart_item_addon_routes import router as cart_item_addon_router


# Ensure all models are imported and mappers are configured
models.Base.metadata.create_all(bind=engine)
configure_mappers()  # Explicitly configure all mappers


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


# Include original routers
app.include_router(routes.user_router)
app.include_router(routes.vendor_router)
app.include_router(routes.item_router)

# Include new entity routers
app.include_router(item_category_router)
app.include_router(delivery_address_router)
app.include_router(rider_router)
app.include_router(item_addon_group_router)
app.include_router(item_addon_router)
app.include_router(item_variation_router)
app.include_router(order_router)
app.include_router(cart_router)
app.include_router(wallet_router)

# Include missing model routers
app.include_router(order_item_router)
app.include_router(order_item_addon_router)
app.include_router(order_tracking_router)
app.include_router(cart_item_router)
app.include_router(cart_item_addon_router)