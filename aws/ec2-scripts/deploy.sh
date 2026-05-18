#!/bin/bash
# AWS EC2 Deployment Script for Solar Panel Classifier
# =====================================================

set -e

PROJECT_NAME="solar-panel-classifier"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO="${ECR_REPO:-$PROJECT_NAME}"
STACK_NAME="${STACK_NAME:-$PROJECT_NAME-stack}"

echo "=========================================="
echo "Solar Panel Classifier — AWS Deployment"
echo "=========================================="

# 1. Build Docker image
echo "[1/6] Building Docker image..."
docker build -f docker/Dockerfile -t $PROJECT_NAME:latest .

# 2. Authenticate with ECR
echo "[2/6] Authenticating with Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com

# 3. Tag and push image
echo "[3/6] Pushing image to ECR..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO"
docker tag $PROJECT_NAME:latest $ECR_URI:latest
docker tag $PROJECT_NAME:latest $ECR_URI:v1.0.0
docker push $ECR_URI:latest
docker push $ECR_URI:v1.0.0

# 4. Upload model to S3
echo "[4/6] Uploading model artifacts to S3..."
S3_BUCKET="$PROJECT_NAME-models-$ACCOUNT_ID"
aws s3 sync models/ s3://$S3_BUCKET/production/ --exclude "*.gitkeep"

# 5. Terraform apply
echo "[5/6] Deploying infrastructure with Terraform..."
cd terraform
terraform init
terraform apply -auto-approve -var="environment=production"

# 6. Get outputs
echo "[6/6] Deployment complete!"
echo ""
echo "Load Balancer URL: $(terraform output -raw alb_dns_name)"
echo "ECR Repository:    $(terraform output -raw ecr_repository_url)"
echo "S3 Model Bucket:   $(terraform output -raw s3_bucket_name)"
echo ""
echo "Next steps:"
echo "  - Configure DNS to point to the ALB"
echo "  - Deploy Kubernetes manifests: kubectl apply -k k8s/overlays/prod"
