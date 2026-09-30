from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.rate_limit import limiter
from app.routers import dashboard, devices, events, items, redemptions, students


def create_app() -> FastAPI:
    app = FastAPI(title="CTF Fridge API", version="1.0.0")

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "internal_error", "message": str(exc), "details": {}}},
        )

    app.include_router(students.router)
    app.include_router(devices.router)
    app.include_router(events.router)
    app.include_router(dashboard.router)
    app.include_router(items.router)
    app.include_router(redemptions.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
