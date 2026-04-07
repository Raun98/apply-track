from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.api import api_router
from app.api.deps import get_db, get_current_user_ws
from app.database import AsyncSessionLocal
from app.services.websocket_manager import websocket_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"Starting {settings.APP_NAME}")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered job application tracking system",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS middleware - must be added before routes
# In production, CORS_ORIGINS should be set as comma-separated URLs in environment
# Example: CORS_ORIGINS=https://myapp.railway.app,https://www.myapp.com
cors_origins = settings.CORS_ORIGINS

# Also add FRONTEND_URL if it's different from CORS_ORIGINS
if settings.FRONTEND_URL and settings.FRONTEND_URL not in cors_origins:
    cors_origins = cors_origins + [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include API routes
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

        await websocket_manager.connect(websocket, user.id)

        try:
            while True:
                # Keep connection alive and handle client messages
                data = await websocket.receive_json()

                # Handle ping/pong
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket, user.id)
        except Exception as e:
            print(f"WebSocket error: {e}")
            websocket_manager.disconnect(websocket, user.id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
