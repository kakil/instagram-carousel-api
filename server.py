from fastapi import FastAPI
from datetime import datetime
import uvicorn

# Try importing from your app package
try:
    from app.core.config import settings
    config_import_success = True
except Exception as e:
    config_import_success = False
    config_error = str(e)

# Add this to the imports section in server.py
try:
    from app.api.v1.endpoints import router as api_router
    router_import_success = True
except Exception as e:
    router_import_success = False
    router_error = str(e)

app = FastAPI(
    title="Instagram Carousel Generator API - Test",
    description="Testing imports from app package",
    version="1.0.0"
)


@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config_import": config_import_success,
        "router_import": router_import_success,
        "config_error": config_error if not config_import_success else None,
        "router_error": router_error if not router_import_success else None
    }

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=5001,
        reload=True
    )