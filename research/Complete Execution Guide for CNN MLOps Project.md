🎯 Complete Execution Guide for CNN MLOps Project
PHASE 1: Environment Setup (One-time setup)
Step 1: Verify Prerequisites
Open terminal in VS Code (Ctrl+ ``) and check:
bash
Copy

# Check Python version (need 3.9+)
python --version

# Check if pip is installed
pip --version

# Check if Git is installed
git --version

# Check Docker (optional, for containerization)
docker --version

# Check AWS CLI (for cloud deployment)
aws --version

What this does: Ensures you have the required tools installed before starting.
Step 2: Create Virtual Environment
bash
Copy

# Navigate to your project folder
cd cnn_mlops_project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# For Windows:
venv\Scripts\activate

# For Mac/Linux:
source venv/bin/activate

What this does: Creates an isolated Python environment so your project dependencies don't conflict with other projects.
You'll see: Your terminal prompt changes to show (venv) at the beginning.
Step 3: Install Dependencies
bash
Copy

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt

What this does: Downloads and installs all required Python packages (PyTorch, FastAPI, MLflow, etc.).
This takes: 5-10 minutes depending on your internet speed.
Step 4: Install Pre-commit Hooks (Optional but recommended)
bash
Copy

pre-commit install

What this does: Automatically checks your code quality before each commit.
PHASE 2: Project Configuration
Step 5: Create Required Directories
bash
Copy

# Create data directories
mkdir -p data/raw data/processed data/train data/val data/test

# Create model directory
mkdir -p models checkpoints logs mlruns

# Create empty files to keep directories in git
touch data/raw/.gitkeep models/.gitkeep logs/.gitkeep

What this does: Creates the folder structure where your data and models will be stored.
Step 6: Set Up Environment Variables
Create a file named .env in your project root:
bash
Copy

# Windows
notepad .env

# Mac/Linux
nano .env

Add this content:
env
Copy

# API Configuration
MODEL_PATH=models/best_model.pt
CLASS_NAMES_PATH=config/class_names.txt
LOG_LEVEL=INFO

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000

# AWS Configuration (only if using AWS)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Database (for MLflow)
DATABASE_URL=sqlite:///mlflow.db

What this does: Stores configuration settings that your application will read.
PHASE 3: Data Preparation
Step 7: Prepare Your Dataset
Option A: Use Sample Data (for testing)
Create a Python script create_sample_data.py:
Python
Copy

import os
from PIL import Image
import numpy as np

def create_sample_dataset(base_dir="data/raw", num_classes=3, images_per_class=10):
    """
    Create a sample dataset with random colored images
    """
    classes = ["cat", "dog", "bird"]
    
    for i, class_name in enumerate(classes[:num_classes]):
        class_dir = os.path.join(base_dir, class_name)
        os.makedirs(class_dir, exist_ok=True)
        
        for j in range(images_per_class):
            # Create random colored image
            img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            
            img_path = os.path.join(class_dir, f"{class_name}_{j}.jpg")
            img.save(img_path)
            print(f"Created: {img_path}")

if __name__ == "__main__":
    create_sample_dataset()
    print("Sample dataset created successfully!")

Run it:
bash
Copy

python create_sample_data.py

What this does: Creates fake images for testing your pipeline without needing real data.
Option B: Use Your Own Images
Organize your images like this:
plain
Copy

data/raw/
├── cat/
│   ├── cat001.jpg
│   ├── cat002.jpg
│   └── ...
├── dog/
│   ├── dog001.jpg
│   ├── dog002.jpg
│   └── ...
└── bird/
    ├── bird001.jpg
    └── ...

Step 8: Split Data into Train/Val/Test
Create split_data.py:
Python
Copy

from src.data.dataset import split_dataset

# Split data (70% train, 15% val, 15% test)
split_dataset(
    data_dir="data/raw",
    output_dir="data",
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15,
    seed=42
)

Run it:
bash
Copy

python split_data.py

What this does: Splits your data into three sets:

    Training set: Used to train the model (70%)
    Validation set: Used to tune hyperparameters (15%)
    Test set: Used to evaluate final performance (15%)

Step 9: Create Class Names File
bash
Copy

# Create class names file
echo -e "cat\ndog\nbird" > config/class_names.txt

What this does: Tells the model what classes to predict.
PHASE 4: Training the Model
Step 10: Start MLflow Tracking Server (Terminal 1)
Open a new terminal (keep it running):
bash
Copy

# Navigate to project
cd cnn_mlops_project
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start MLflow server
mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000

What this does: Starts a web server to track your experiments.
Access it: Open http://localhost:5000 in your browser.
Step 11: Start Training (Terminal 2)
Open another new terminal:
bash
Copy

cd cnn_mlops_project
source venv/bin/activate

# Run training
python -m src.training.train --config config/training.yaml --epochs 5 --batch-size 4

What this does: Trains your CNN model.
Parameters explained:

    --epochs 5: Train for 5 rounds (use 50-100 for real training)
    --batch-size 4: Process 4 images at once (reduce if you get memory errors)

Expected output:
plain
Copy

Epoch 0: Train Loss: 1.2345, Train Acc: 0.4567, Val Loss: 1.1234, Val Acc: 0.5678
Epoch 1: Train Loss: 0.9876, Train Acc: 0.6543, Val Loss: 0.8765, Val Acc: 0.7654
...
Checkpoint saved: checkpoints/checkpoint_epoch_4.pt

Step 12: Verify Training Results

    Check MLflow UI (http://localhost:5000):
        Click on your experiment
        View metrics (loss, accuracy curves)
        See logged parameters
    Check checkpoints folder:
    bash
    Copy

    ls checkpoints/
    # You should see: checkpoint_epoch_0.pt, best_model.pt, etc.

PHASE 5: Running the API Server
Step 13: Copy Best Model
bash
Copy

# Copy best model to models folder
cp checkpoints/best_model.pt models/best_model.pt

Step 14: Start API Server (Terminal 3)
Open another new terminal:
bash
Copy

cd cnn_mlops_project
source venv/bin/activate

# Start API server
python -m src.api.main

What this does: Starts the FastAPI server to serve predictions.
Expected output:
plain
Copy

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

Test it: Open http://localhost:8000/docs in your browser (interactive API documentation).
Step 15: Test API Endpoints
Test 1: Health Check
bash
Copy

curl http://localhost:8000/health

Expected response:
JSON
Copy

{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "v1.0.0",
  "device": "cpu",
  "uptime_seconds": 45.3
}

Test 2: Predict Single Image
Create test_api.py:
Python
Copy

import requests

def test_prediction(image_path):
    url = "http://localhost:8000/api/v1/predict"
    
    with open(image_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Prediction: {result['prediction']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Inference time: {result['inference_time_ms']:.2f} ms")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Test with any image from your dataset
    test_prediction("data/test/cat/cat_0.jpg")

Run it:
bash
Copy

python test_api.py

PHASE 6: Running Streamlit UI
Step 16: Start Streamlit (Terminal 4)
Open another new terminal:
bash
Copy

cd cnn_mlops_project
source venv/bin/activate

# Start Streamlit
streamlit run streamlit_app/main.py

What this does: Starts the web interface.
Access it: Open http://localhost:8501 in your browser.
Features you'll see:

    Upload image button
    Drag-and-drop area
    Prediction results with confidence scores
    Charts showing probability distribution

PHASE 7: Docker Deployment (Optional)
Step 17: Build and Run with Docker
Prerequisites: Docker Desktop installed and running.
bash
Copy

# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

What this does: Runs your entire stack in containers:

    API: http://localhost:8000
    Streamlit: http://localhost:8501
    MLflow: http://localhost:5000
    Grafana: http://localhost:3000 (admin/admin)

PHASE 8: Testing
Step 18: Run Test Suite
bash
Copy

# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

What this does: Verifies your code works correctly.
PHASE 9: AWS Deployment (Advanced)
Step 19: Deploy Infrastructure
bash
Copy

cd terraform

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply

What this does: Creates AWS resources (EKS cluster, S3 buckets, etc.).
Step 20: Deploy to Kubernetes
bash
Copy

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name cnn-mlops-cluster

# Deploy to development
kubectl apply -k k8s/overlays/dev

# Check status
kubectl get pods -n cnn-mlops-dev
kubectl get svc -n cnn-mlops-dev

📋 Quick Reference: Common Commands
Table
Task	Command
Activate virtual env	source venv/bin/activate or venv\Scripts\activate
Start MLflow	mlflow server --backend-store-uri sqlite:///mlflow.db
Train model	python -m src.training.train --config config/training.yaml
Start API	python -m src.api.main
Start Streamlit	streamlit run streamlit_app/main.py
Run tests	pytest tests/ -v
Format code	black src/ tests/
Docker up	docker-compose up -d
Docker down	docker-compose down

---
| Task                 | Command                                                      |
| -------------------- | ------------------------------------------------------------ |
| Activate virtual env | `source venv/bin/activate` or `venv\Scripts\activate`        |
| Start MLflow         | `mlflow server --backend-store-uri sqlite:///mlflow.db`      |
| Train model          | `python -m src.training.train --config config/training.yaml` |
| Start API            | `python -m src.api.main`                                     |
| Start Streamlit      | `streamlit run streamlit_app/main.py`                        |
| Run tests            | `pytest tests/ -v`                                           |
| Format code          | `black src/ tests/`                                          |
| Docker up            | `docker-compose up -d`                                       |
| Docker down          | `docker-compose down`                                        |

---

🐛 Troubleshooting
Issue 1: "ModuleNotFoundError"
bash
Copy

# Solution: Make sure you're in virtual environment
source venv/bin/activate

# Install missing package
pip install <package-name>

Issue 2: "CUDA out of memory"
Python
Copy

# In training config, reduce batch size
batch_size: 2  # Instead of 32

Issue 3: "Port already in use"
bash
Copy

# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8000   # Windows

Issue 4: Model not loading
bash
Copy

# Check if model file exists
ls models/best_model.pt

# If not, copy from checkpoints
cp checkpoints/best_model.pt models/

🎓 Learning Path

    Week 1: Understand the code structure, run training locally
    Week 2: Experiment with different models, hyperparameters
    Week 3: Set up MLflow tracking, monitor experiments
    Week 4: Deploy API, test with real images
    Week 5: Docker containerization
    Week 6: AWS deployment (if needed)

📚 Key Files to Understand
Table
File	Purpose
src/models/cnn_classifier.py	Model architecture
src/training/train.py	Training loop
src/api/main.py	FastAPI server
streamlit_app/main.py	Web interface
config/training.yaml	Training configuration
docker-compose.yml	Local orchestration

---
| File                           | Purpose                |
| ------------------------------ | ---------------------- |
| `src/models/cnn_classifier.py` | Model architecture     |
| `src/training/train.py`        | Training loop          |
| `src/api/main.py`              | FastAPI server         |
| `streamlit_app/main.py`        | Web interface          |
| `config/training.yaml`         | Training configuration |
| `docker-compose.yml`           | Local orchestration    |

---
This guide should get you from zero to a fully running CNN MLOps system! Start with Phase 1-3, then gradually move to more advanced features.