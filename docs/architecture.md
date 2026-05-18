# Solar Panel Classifier — Architecture

## System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  FastAPI Service│────▶│  TensorFlow     │
│   (Port 8501)   │     │  (Port 8000)    │     │  Model          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        └───────────────────────────────────────────────┘
                    (Direct Python API)
```

## Components

### 1. Data Layer
- **Source:** `Data/` directory with 6 class subfolders
- **Preprocessing:** 224×224 resize, EfficientNet/MobileNet normalization
- **Augmentation:** Random flip, rotation, zoom

### 2. Model Layer
- **EfficientNetB0** (best): ~81.4% val accuracy, 4.2M params
- **MobileNetV2** (lightweight): ~75.7% val accuracy, 2.4M params
- **Format:** Keras v3 (`.keras`) + HDF5 fallback (`.h5`)

### 3. API Layer (FastAPI)
- `POST /api/v1/predict` — Single image inference
- `POST /api/v1/predict/batch` — Batch inference
- `GET /health` — Service health check
- `GET /model/info` — Model metadata

### 4. UI Layer (Streamlit)
- Image upload & preview
- Top-K prediction display
- Confidence bar charts
- Inference latency benchmark

### 5. Deployment Layer
- **Docker:** Multi-stage build for production
- **Docker Compose:** Local orchestration (API + Streamlit)
- **GitHub Actions:** CI/CD with lint, test, build stages

## Data Flow

1. User uploads image via Streamlit or HTTP API
2. Image is saved to temporary file
3. `SolarPanelClassifier.predict()` loads & preprocesses image
4. TensorFlow model runs inference
5. Results returned with class names, confidence scores, latency
