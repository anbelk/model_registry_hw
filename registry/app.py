from contextlib import asynccontextmanager

from fastapi import FastAPI

from registry.api.models_router import router as models_router
from registry.api.versions_router import router as versions_router
from registry.config import get_settings
from registry.storage import Storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not get_settings().skip_storage_init:
        storage = Storage()
        storage.ensure_bucket()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Model Registry", version="1.0.0", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(models_router)
    app.include_router(versions_router)
    return app


app = create_app()
