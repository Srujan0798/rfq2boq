"""FastAPI application — RFQ2BOQ internship project."""

from __future__ import annotations

import logging

from config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import (
    boq,
    cost,
    export_routes,
    extract,
    llm_routes,
    review,
    risk_routes,
    upload,
)
from src.api.schemas import HealthResponse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

app = FastAPI(
    title="RFQ2BOQ API",
    version="0.1.0",
    description="Extract structured Bill of Quantities from construction RFQ PDFs.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ALLOWED_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


for router_module in (extract, upload, boq, cost, llm_routes, review, risk_routes, export_routes):
    if hasattr(router_module, "router"):
        app.include_router(router_module.router)


@app.get("/", response_model=dict)
async def root() -> dict:
    return {"message": "RFQ2BOQ API", "version": "0.1.0"}


@app.get("/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


# Legacy alias for older clients
@app.get("/api/health", response_model=HealthResponse)
async def health_legacy() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")
