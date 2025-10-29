"""Re-export existing vendor dashboard router so it appears under the views namespace
This file re-exports the router defined in `app.routes.vendor_dashboard_routes`.
"""
from ..vendor_dashboard_routes import router as vendor_dashboard_router

# Expose `router` for main app to include
router = vendor_dashboard_router