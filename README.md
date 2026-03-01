### Classificarion_CNN_2D_MLOPS_End-to-End_project 
---


🏗️ Complete Architecture

1. Deep Learning Pipeline

    Models: ResNet50/18, EfficientNet-B0/B4, Vision Transformer
    Training: Distributed training, mixed precision (FP16), gradient clipping
    Augmentation: Albumentations with geometric & photometric transforms
    Optimization: AdamW, Cosine annealing, OneCycle LR, Early stopping

2. FastAPI Inference Service (src/api/main.py)

---

### Project Structure

----
classification-cnn-2d-mlops/ 
├── .github/workflows/ci-cd.yml    # 8-stage CI/CD 
├── docker/                         # Multi-stage Dockerfiles 
├── k8s/base/                       # K8s manifests 
├── k8s/overlays/dev,prod/          # Environment configs 
├── terraform/                      # AWS infrastructure 
├── src/ 
│   ├── api/main.py                # FastAPI (400+ lines) 
│   ├── models/cnn_classifier.py   # ResNet/EfficientNet 
│   ├── training/train.py          # Trainer (350+ lines) 
│   ├── data/dataset.py            # Data pipeline 
│   ├── monitoring/drift_detector.py # Drift detection 
│   └── utils/                      # Logger, metrics, config 
├── streamlit_app/main.py          # Web UI (400+ lines) 
├── tests/                          # Unit, Integration, E2E 
├── docs/                           # Architecture & API docs 
├── docker-compose.yml              # Local development 
├── Makefile                        # Automation 
└── pyproject.toml                  # Modern Python packaging 
 

---


🔒 Security Features

    IAM Roles for Service Accounts (IRSA)
    Network policies & Security groups
    Secrets encryption (AWS Secrets Manager)
    Container vulnerability scanning (Trivy)
    TLS 1.3, Non-root containers
    Private subnets for databases

---

💰 Cost Optimization

    Spot Instances: 70% savings on training
    S3 Intelligent-Tiering: Automatic storage class transition
    Right-sizing: Resource requests/limits
    Auto-shutdown: Dev environment scheduling

---

📈 Scalability 

| Feature          | Configuration                       |
| ---------------- | ----------------------------------- |
| **HPA**          | 3-20 replicas (CPU 70%, Memory 80%) |
| **Latency**      | p99 < 100ms                         |
| **Throughput**   | 1000+ req/sec                       |
| **Availability** | 99.9%                               |


This is a production-grade, enterprise-ready MLOps platform that follows industry best practices for deep learning deployment on AWS with Kubernetes. 

🚀 Quick Start Commands

# 1. Setup environment
make setup

# 2. Start local development stack
make docker-up
# Services: API (8000), Streamlit (8501), MLflow (5000), Grafana (3000)

# 3. Run training
make train

# 4. Run tests
make test

# 5. Deploy to AWS
cd terraform && terraform apply
kubectl apply -k k8s/overlays/prod