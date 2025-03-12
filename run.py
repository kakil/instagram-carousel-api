import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=5001,
        reload=settings.DEBUG
    )