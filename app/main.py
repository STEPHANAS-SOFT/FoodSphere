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

# Import comprehensive view routers from the new `routes.views` package
from .routes.views.search_views import router as search_router
from .routes.views.order_views import router as enhanced_order_router
from .routes.views.tracking_views import router as tracking_router
from .routes.views.vendor_dashboard_view import router as vendor_dashboard_router
from .routes.views.rider_views import router as rider_management_router
from .routes.views.payment_views import router as payment_router
from .routes.views.promotion_views import router as promotion_router
from .routes.views.analytics_views import router as analytics_router
from .routes.views.notifications_views import router as notifications_router
from .routes.views.utils_views import router as system_router
from .routes.views.item_views import router as item_views_router
from .routes.views.user_views import router as user_views_router
from .routes.views.vendor_views import router as vendor_views_router


# Ensure all models are imported and mappers are configured
models.Base.metadata.create_all(bind=engine)
configure_mappers()  # Explicitly configure all mappers


# Initialize FastAPI app
app = FastAPI(
    title="MetroMart",
    description="MetroMart delivery App",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/openapi.json",
    redoc_url="/api/redoc",
    root_path="/metromart"
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
        "message": "MetroMart Food Delivery API",
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

# Include comprehensive view routers
app.include_router(search_router)
app.include_router(enhanced_order_router)
app.include_router(tracking_router)
app.include_router(vendor_dashboard_router)
app.include_router(rider_management_router)
app.include_router(payment_router)
app.include_router(promotion_router)
app.include_router(analytics_router)
app.include_router(notifications_router)
app.include_router(system_router)
app.include_router(item_views_router)
app.include_router(user_views_router)
app.include_router(vendor_views_router)