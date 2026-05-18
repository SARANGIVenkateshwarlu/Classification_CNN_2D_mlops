# Solar Panel Classifier — API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### `GET /`
Service info.

**Response:**
```json
{
  "service": "Solar Panel Classifier API",
  "version": "0.1.0",
  "docs": "/docs"
}
```

### `GET /health`
Health check.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "trained_effnet_finetune",
  "timestamp": "2024-01-01T00:00:00"
}
```

### `GET /model/info`
Model metadata.

**Response:**
```json
{
  "model_name": "trained_effnet_finetune.keras",
  "classes": ["Bird-drop", "Clean", "Dusty", "Electrical-damage", "Physical-Damage", "Snow-Covered"],
  "num_classes": 6,
  "input_size": "224 × 224",
  "loaded_at": "2024-01-01T00:00:00"
}
```

### `POST /api/v1/predict`
Single image classification.

**Parameters:**
- `file` (UploadFile, required): Image file
- `top_k` (int, optional): Number of top predictions (default: 3)

**Response:**
```json
{
  "prediction": "Clean",
  "confidence": 0.9857,
  "probabilities": {
    "Bird-drop": 0.0061,
    "Clean": 0.9857,
    "Dusty": 0.0057,
    ...
  },
  "inference_time_ms": 45.23,
  "model_name": "trained_effnet_finetune",
  "timestamp": "2024-01-01T00:00:00"
}
```

### `POST /api/v1/predict/batch`
Batch image classification.

**Parameters:**
- `files` (List[UploadFile], required): Image files
- `top_k` (int, optional): Number of top predictions (default: 3)

**Response:**
```json
{
  "results": [...],
  "total_images": 5,
  "total_time_ms": 234.56
}
```

## Interactive Docs
Launch the API and visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
