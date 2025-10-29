"""
FoodSphere API Views Package

This package contains all the enhanced API endpoint views for the FoodSphere food delivery platform.
All views are organized by functional area and are designed to work with Firebase authentication.

Available View Modules:
- search_views: Search vendors, items, nearby restaurants, menu browsing
- item_views: Comprehensive item management, pricing, availability, variations
- order_views: Enhanced order management, calculations, history, ratings
- tracking_views: Real-time order tracking and rider location updates
- rider_views: Rider operations - available orders, deliveries, earnings
- payment_views: Payment processing and payment method management (stubs)
- promotion_views: Coupons, promotions, and loyalty features (stubs)
- analytics_views: Admin dashboard and reporting endpoints (stubs)
- notifications_views: Push notifications and support chat (stubs)
- utils_views: System health checks and metrics
- vendor_dashboard_view: Re-export of existing vendor dashboard functionality

Note: Authentication endpoints are excluded as Firebase handles login/registration.
"""

# Export all routers for convenience
from .search_views import router as search_router
from .order_views import router as order_router
from .tracking_views import router as tracking_router
from .rider_views import router as rider_router
from .payment_views import router as payment_router
from .promotion_views import router as promotion_router
from .analytics_views import router as analytics_router
from .notifications_views import router as notifications_router
from .utils_views import router as utils_router
from .vendor_dashboard_view import router as vendor_dashboard_router
from .item_views import router as item_router

__all__ = [
    "search_router",
    "order_router", 
    "tracking_router",
    "rider_router",
    "payment_router",
    "promotion_router",
    "analytics_router",
    "notifications_router",
    "utils_router",
    "vendor_dashboard_router",
    "item_router"
]