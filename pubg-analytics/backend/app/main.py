import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db, init_db
from .exceptions import (
    InvalidPUBGDataError,
    PlayerNotFoundError,
    PUBGAPIError,
    PUBGAPIUnavailableError,
    RateLimitedError,
)
from .pubg_client import PUBGClient
from .schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse, HealthResponse, VersionResponse
from .service import AnalysisService
from .telemetry import configure_telemetry

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_runtime()
    init_db()
    yield


app = FastAPI(
    title="PUBG Match Analytics",
    version="1.0.0",
    description="Analyze the latest Solo FPP PUBG matches for a player.",
    lifespan=lifespan,
)
configure_telemetry(app)
STATIC_DIR = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    if settings.pubg_api_key is None:
        raise RuntimeError("PUBG_API_KEY must be configured before analyzing matches.")
    client = PUBGClient(
        api_key=settings.pubg_api_key,
        platform=settings.pubg_platform,
        base_url=settings.pubg_api_base_url,
        timeout=settings.pubg_api_timeout,
    )
    return AnalysisService(client=client, db=db, mode=settings.pubg_mode)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", response_model=HealthResponse, responses={200: {"model": HealthResponse}})
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    return VersionResponse(commit_sha=os.getenv("RAILWAY_GIT_COMMIT_SHA", "unknown"))


@app.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"description": "Database unavailable"}},
)
def readiness(db: Session = Depends(get_db)) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Database readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(status_code=200, content={"status": "ok"})


@app.middleware("http")
async def request_logging(request: Request, call_next):
    started_at = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        logger.info(
            "HTTP request completed",
            extra={
                "http_method": request.method,
                "http_route": getattr(route, "path", request.url.path),
                "http_status_code": status_code,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 3),
            },
        )


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def analyze(payload: AnalyzeRequest, service: AnalysisService = Depends(get_analysis_service)) -> AnalyzeResponse:
    try:
        return await service.analyze(payload.nickname)
    except PlayerNotFoundError as exc:
        logger.warning("Player not found")
        raise HTTPException(status_code=404, detail={"code": "PLAYER_NOT_FOUND", "message": str(exc)}) from exc
    except RateLimitedError as exc:
        logger.warning("PUBG API rate limit reached")
        raise HTTPException(status_code=429, detail={"code": "RATE_LIMITED", "message": "PUBG API rate limit reached"}) from exc
    except InvalidPUBGDataError as exc:
        logger.warning("Invalid PUBG data: %s", exc)
        raise HTTPException(status_code=502, detail={"code": "PUBG_API_ERROR", "message": "PUBG API returned incomplete match data"}) from exc
    except PUBGAPIUnavailableError as exc:
        logger.error("PUBG API unavailable: %s", exc)
        raise HTTPException(status_code=503, detail={"code": "PUBG_API_UNAVAILABLE", "message": "PUBG API is temporarily unavailable"}) from exc
    except PUBGAPIError as exc:
        logger.error("PUBG API error: %s", exc)
        raise HTTPException(status_code=502, detail={"code": "PUBG_API_ERROR", "message": "PUBG API request failed"}) from exc


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    from fastapi.responses import JSONResponse

    detail = exc.detail
    if isinstance(detail, dict) and {"code", "message"}.issubset(detail):
        return JSONResponse(status_code=exc.status_code, content={"error": detail})
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "VALIDATION_ERROR", "message": str(detail)}})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    from fastapi.responses import JSONResponse

    messages = []
    for error in exc.errors():
        messages.append(error.get("msg", "Invalid request"))
    message = "; ".join(messages)
    return JSONResponse(status_code=400, content={"error": {"code": "VALIDATION_ERROR", "message": message}})
