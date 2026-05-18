"""
Solar Panel Classifier — FastAPI Inference Service
===================================================
Production-ready REST API for image classification.

Endpoints:
    POST /api/v1/predict       — Single image prediction
    POST /api/v1/predict/batch — Batch prediction
    GET  /health               — Health check
    GET  /model/info           — Model metadata
    GET  /metrics              — Prometheus metrics

Run:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Lazy TF import to avoid loading on module import
def _get_classifier(model_path: Optional[str] = None):
    from src.solar_panel_classifier.predictor import SolarPanelClassifier
    from src.solar_panel_classifier.config import DEFAULT_MODEL_PATH

    path = model_path or os.getenv("MODEL_PATH") or str(DEFAULT_MODEL_PATH)
    return SolarPanelClassifier(model_path=path)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    probabilities: dict
    inference_time_ms: float
    model_name: str
    timestamp: str


class BatchPredictionResponse(BaseModel):
    results: List[PredictionResponse]
    total_images: int
    total_time_ms: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    timestamp: str


class ModelInfoResponse(BaseModel):
    model_name: str
    classes: List[str]
    num_classes: int
    input_size: str
    loaded_at: str


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Solar Panel Classifier API",
    description="REST API for solar panel condition classification",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
_app_state = {
    "classifier": None,
    "loaded_at": None,
}


def _get_model():
    """Lazy-load model on first request."""
    if _app_state["classifier"] is None:
        _app_state["classifier"] = _get_classifier()
        _app_state["loaded_at"] = datetime.now(timezone.utc).isoformat()
    return _app_state["classifier"]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Solar Panel Classifier API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    classifier = _app_state["classifier"]
    model_loaded = classifier is not None
    model_name = "none"
    if classifier is not None:
        model_name = Path(classifier.model_path).stem
    return HealthResponse(
        status="healthy",
        model_loaded=model_loaded,
        model_name=model_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model"])
async def model_info():
    classifier = _get_model()
    return ModelInfoResponse(
        model_name=Path(classifier.model_path).name,
        classes=classifier.class_names,
        num_classes=classifier.num_classes,
        input_size="224 × 224",
        loaded_at=_app_state["loaded_at"] or datetime.utcnow().isoformat(),
    )


@app.post("/api/v1/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(
    file: UploadFile = File(..., description="Image file to classify"),
    top_k: int = 3,
):
    """Classify a single image."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    classifier = _get_model()

    # Save uploaded file temporarily
    temp_path = Path(f"_temp_api_{file.filename}")
    try:
        contents = await file.read()
        temp_path.write_bytes(contents)

        t0 = time.perf_counter()
        preds = classifier.predict(str(temp_path), top_k=top_k)
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000

        # Build full probability dict (pad missing classes with 0.0)
        probs = {cls: 0.0 for cls in classifier.class_names}
        for cls, conf in preds:
            probs[cls] = conf

        top = preds[0]
        return PredictionResponse(
            prediction=top[0],
            confidence=top[1],
            probabilities=probs,
            inference_time_ms=latency_ms,
            model_name=Path(classifier.model_path).stem,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.post(
    "/api/v1/predict/batch",
    response_model=BatchPredictionResponse,
    tags=["Prediction"],
)
async def predict_batch(
    files: List[UploadFile] = File(..., description="Image files to classify"),
    top_k: int = 3,
):
    """Classify multiple images in one request."""
    classifier = _get_model()
    results = []
    total_t0 = time.perf_counter()

    for file in files:
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail=f"{file.filename} is not an image"
            )

        temp_path = Path(f"_temp_api_{file.filename}")
        try:
            contents = await file.read()
            temp_path.write_bytes(contents)

            t0 = time.perf_counter()
            preds = classifier.predict(str(temp_path), top_k=top_k)
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000

            probs = {cls: 0.0 for cls in classifier.class_names}
            for cls, conf in preds:
                probs[cls] = conf

            top = preds[0]
            results.append(
                PredictionResponse(
                    prediction=top[0],
                    confidence=top[1],
                    probabilities=probs,
                    inference_time_ms=latency_ms,
                    model_name=Path(classifier.model_path).stem,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
        finally:
            if temp_path.exists():
                temp_path.unlink()

    total_t1 = time.perf_counter()
    return BatchPredictionResponse(
        results=results,
        total_images=len(results),
        total_time_ms=(total_t1 - total_t0) * 1000,
    )


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Pre-load model on startup if MODEL_PRELOAD is set."""
    if os.getenv("MODEL_PRELOAD", "true").lower() == "true":
        _get_model()
