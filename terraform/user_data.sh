#!/bin/bash
# EC2 User Data — Solar Panel Classifier API Setup
# ================================================

set -e

PROJECT_NAME="${project_name}"
LOG_FILE="/var/log/solar-panel-setup.log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date)] Starting setup for $PROJECT_NAME"

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install docker-compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Pull and run application
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

mkdir -p /opt/$PROJECT_NAME
cd /opt/$PROJECT_NAME

cat > docker-compose.yml << 'EOF'
version: "3.9"
services:
  api:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/solar-panel-classifier:latest
    ports:
      - "8000:8000"
    environment:
      - MODEL_PATH=/app/models/trained_effnet_finetune.keras
      - MODEL_PRELOAD=true
    volumes:
      - ./models:/app/models:ro
    restart: always
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF

docker-compose up -d

echo "[$(date)] Setup complete"
