from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.api.api import api_router
from app.api.deps import get_db, get_current_user_ws
from app.database import AsyncSessionLocal
from app.services.websocket_manager import manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}")
    await manager.startup()
    yield
    await manager.shutdown()
    logger.info(f"Shutting down {settings.APP_NAME}")


is_production = settings.ENVIRONMENT == "production"

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered job application tracking system",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if not is_production else None,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if not is_production else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if not is_production else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins = settings.CORS_ORIGINS

if settings.FRONTEND_URL and settings.FRONTEND_URL not in cors_origins:
    cors_origins = cors_origins + [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME}


@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    async with AsyncSessionLocal() as db:
        user = await get_current_user_ws(websocket, db)

        if not user:
            await websocket.close(code=4001)
            return

        await manager.connect(user.id, websocket)

        try:
            while True:
                data = await websocket.receive_json()

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            manager.disconnect(user.id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(user.id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
