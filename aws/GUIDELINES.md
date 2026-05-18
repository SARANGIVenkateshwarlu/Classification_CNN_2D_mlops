# AWS Enterprise Deployment Guidelines

## Solar Panel Classifier — Complete AWS Integration & Deployment

This document provides comprehensive, step-by-step instructions for deploying the Solar Panel Classifier on AWS using multiple strategies: **EC2**, **ECS Fargate**, **Lambda**, and **SageMaker**.

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Prerequisites](#-prerequisites)
- [Step 1: AWS Account Setup](#-step-1-aws-account-setup)
- [Step 2: IAM Configuration](#-step-2-iam-configuration)
- [Step 3: Amazon ECR (Container Registry)](#-step-3-amazon-ecr-container-registry)
- [Step 4: Amazon S3 (Model Storage)](#-step-4-amazon-s3-model-storage)
- [Step 5: Deployment Option A — EC2 + Auto Scaling](#-step-5-deployment-option-a--ec2--auto-scaling)
- [Step 6: Deployment Option B — ECS Fargate](#-step-6-deployment-option-b--ecs-fargate)
- [Step 7: Deployment Option C — AWS Lambda](#-step-7-deployment-option-c--aws-lambda)
- [Step 8: Deployment Option D — Amazon SageMaker](#-step-8-deployment-option-d--amazon-sagemaker)
- [Step 9: API Gateway Integration](#-step-9-api-gateway-integration)
- [Step 10: CloudWatch Monitoring](#-step-10-cloudwatch-monitoring)
- [Step 11: CI/CD with AWS CodePipeline](#-step-11-cicd-with-aws-codepipeline)
- [Cost Optimization](#-cost-optimization)
- [Security Best Practices](#-security-best-practices)
- [Troubleshooting](#-troubleshooting)

---

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph Client["Client Applications"]
        A[Web Browser]
        B[Mobile App]
        C[IoT Device]
    end

    subgraph Edge["Edge Layer"]
        D[CloudFront CDN]
        E[AWS WAF]
    end

    subgraph API["API Layer"]
        F[API Gateway<br/>Rate Limit | Auth]
        G[Application Load Balancer]
    end

    subgraph Compute["Compute Layer"]
        H[ECS Fargate<br/>FastAPI Containers]
        I[EC2 Auto Scaling<br/>GPU/CPU Instances]
        J[AWS Lambda<br/>Serverless Inference]
        K[SageMaker<br/>Managed Endpoints]
    end

    subgraph Storage["Storage Layer"]
        L[(S3<br/>Model Artifacts)]
        M[(EFS<br/>Shared Storage)]
        N[(DynamoDB<br/>Inference Logs)]
    end

    subgraph Registry["Registry"]
        O[Amazon ECR<br/>Container Images]
    end

    subgraph Monitor["Monitoring"]
        P[CloudWatch<br/>Metrics & Logs]
        Q[X-Ray<br/>Distributed Tracing]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    E --> G
    F --> H
    F --> J
    G --> I
    G --> H
    H --> K
    I --> K
    J --> L
    K --> L
    H --> M
    I --> M
    H --> N
    I --> N
    J --> N
    O --> H
    O --> I
    H --> P
    I --> P
    J --> P
    K --> P
    H --> Q
    I --> Q
    J --> Q

    style Client fill:#e1f5fe
    style Edge fill:#fff3e0
    style API fill:#e8f5e9
    style Compute fill:#fce4ec
    style Storage fill:#f3e5f5
    style Registry fill:#e0f2f1
    style Monitor fill:#fff8e1
```

---

## 📋 Prerequisites

### Required Tools

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
sudo ./aws/install --update
aws --version

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install ECS CLI
curl -Lo /usr/local/bin/ecs-cli https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-linux-amd64-latest
chmod +x /usr/local/bin/ecs-cli

# Verify installations
aws --version
docker --version
ecs-cli --version
```

### AWS Configuration

```bash
# Configure credentials (use IAM user with programmatic access)
aws configure
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region name: us-east-1
# Default output format: json

# Verify identity
aws sts get-caller-identity
# Expected: Account, UserId, Arn
```

### Required AWS Service Quotas

| Service | Quota | Request If Needed |
|---------|-------|-------------------|
| EC2 | t3.medium or higher | Default usually sufficient |
| ECS | Fargate vCPU | 256 vCPU default |
| Lambda | 10 GB memory | Default sufficient |
| SageMaker | ml.m5.large | May need increase |
| API Gateway | 10,000 RPS | Default sufficient |

---

## Step 1: AWS Account Setup

### 1.1 Create S3 Bucket for Terraform State

```bash
export AWS_REGION=us-east-1
export PROJECT_NAME=solar-panel-classifier
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create Terraform state bucket
aws s3api create-bucket \
  --bucket ${PROJECT_NAME}-terraform-state-${ACCOUNT_ID} \
  --region ${AWS_REGION}

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ${PROJECT_NAME}-terraform-state-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ${PROJECT_NAME}-terraform-state-${ACCOUNT_ID} \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket ${PROJECT_NAME}-terraform-state-${ACCOUNT_ID} \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

### 1.2 Create DynamoDB Table for State Locking

```bash
aws dynamodb create-table \
  --table-name ${PROJECT_NAME}-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${AWS_REGION}
```

### 1.3 Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name ${PROJECT_NAME} \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE \
  --region ${AWS_REGION}

# Get repository URI
export ECR_URI=${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}
echo "ECR URI: ${ECR_URI}"
```

### 1.4 Create S3 Bucket for Model Artifacts

```bash
aws s3api create-bucket \
  --bucket ${PROJECT_NAME}-models-${ACCOUNT_ID} \
  --region ${AWS_REGION}

aws s3api put-bucket-versioning \
  --bucket ${PROJECT_NAME}-models-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket ${PROJECT_NAME}-models-${ACCOUNT_ID} \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

# Upload models
aws s3 sync ../models/ s3://${PROJECT_NAME}-models-${ACCOUNT_ID}/production/ \
  --exclude "*.gitkeep"
```

---

## Step 2: IAM Configuration

### 2.1 Create EC2 Instance Role

```bash
# Create trust policy
cat <<EOF > ec2-trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name ${PROJECT_NAME}-ec2-role \
  --assume-role-policy-document file://ec2-trust-policy.json

# Attach managed policies
aws iam attach-role-policy \
  --role-name ${PROJECT_NAME}-ec2-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

aws iam attach-role-policy \
  --role-name ${PROJECT_NAME}-ec2-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

aws iam attach-role-policy \
  --role-name ${PROJECT_NAME}-ec2-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name ${PROJECT_NAME}-ec2-profile

aws iam add-role-to-instance-profile \
  --instance-profile-name ${PROJECT_NAME}-ec2-profile \
  --role-name ${PROJECT_NAME}-ec2-role
```

### 2.2 Create ECS Task Execution Role

```bash
# Create trust policy
cat <<EOF > ecs-trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name ${PROJECT_NAME}-ecs-execution-role \
  --assume-role-policy-document file://ecs-trust-policy.json

aws iam attach-role-policy \
  --role-name ${PROJECT_NAME}-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### 2.3 Create Lambda Execution Role

```bash
cat <<EOF > lambda-trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name ${PROJECT_NAME}-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json

aws iam attach-role-policy \
  --role-name ${PROJECT_NAME}-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name ${PROJECT_NAME}-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

---

## Step 3: Amazon ECR (Container Registry)

### 3.1 Authenticate Docker with ECR

```bash
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_URI}
```

### 3.2 Build and Push Image

```bash
cd ..

# Build production image
docker build -f docker/Dockerfile -t ${PROJECT_NAME}:latest .

# Tag with ECR URI
docker tag ${PROJECT_NAME}:latest ${ECR_URI}:latest
docker tag ${PROJECT_NAME}:latest ${ECR_URI}:v1.0.0

# Push to ECR
docker push ${ECR_URI}:latest
docker push ${ECR_URI}:v1.0.0

# Verify
aws ecr describe-images --repository-name ${PROJECT_NAME} --region ${AWS_REGION}
```

### 3.3 Enable Image Scanning

```bash
aws ecr put-registry-scanning-configuration \
  --scan-type ENHANCED \
  --rules '[{"scanFrequency":"CONTINUOUS_SCAN","repositoryFilters":[{"filter":"*","filterType":"WILDCARD"}]}]' \
  --region ${AWS_REGION}
```

---

## Step 4: Amazon S3 (Model Storage)

### 4.1 Upload Models with Versioning

```bash
# Upload with metadata
aws s3 cp ../models/trained_effnet_finetune.keras \
  s3://${PROJECT_NAME}-models-${ACCOUNT_ID}/production/ \
  --metadata model-type=efficientnet,version=1.0.0

aws s3 cp ../models/mobilenetv2_2.keras \
  s3://${PROJECT_NAME}-models-${ACCOUNT_ID}/production/ \
  --metadata model-type=mobilenetv2,version=1.0.0

# Enable lifecycle policy (move old versions to Glacier)
cat <<EOF > s3-lifecycle.json
{
  "Rules": [
    {
      "ID": "MoveOldVersionsToGlacier",
      "Status": "Enabled",
      "Filter": {"Prefix": ""},
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "GLACIER"
        }
      ],
      "NoncurrentVersionExpiration": {"NoncurrentDays": 365}
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket ${PROJECT_NAME}-models-${ACCOUNT_ID} \
  --lifecycle-configuration file://s3-lifecycle.json
```

### 4.2 Configure Cross-Region Replication (Optional)

```bash
# Create destination bucket in secondary region
aws s3api create-bucket \
  --bucket ${PROJECT_NAME}-models-${ACCOUNT_ID}-replica \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

# Enable replication (requires IAM role with replication permissions)
# See: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html
```

---

## Step 5: Deployment Option A — EC2 + Auto Scaling

### 5.1 Deploy with Terraform (Recommended)

```bash
cd ../terraform

# Initialize with remote backend
cat <<EOF > backend.tf
terraform {
  backend "s3" {
    bucket         = "${PROJECT_NAME}-terraform-state-${ACCOUNT_ID}"
    key            = "infrastructure/terraform.tfstate"
    region         = "${AWS_REGION}"
    encrypt        = true
    dynamodb_table = "${PROJECT_NAME}-terraform-locks"
  }
}
EOF

terraform init
terraform plan -var="environment=production"
terraform apply -auto-approve -var="environment=production"
```

### 5.2 Manual EC2 Deployment (Alternative)

```bash
# Create security group
export SG_ID=$(aws ec2 create-security-group \
  --group-name ${PROJECT_NAME}-sg \
  --description "Security group for Solar Panel Classifier" \
  --vpc-id $(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text) \
  --query 'GroupId' --output text)

# Allow HTTP and HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id ${SG_ID} \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id ${SG_ID} \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids ${SG_ID} \
  --iam-instance-profile Name=${PROJECT_NAME}-ec2-profile \
  --user-data file://ec2-scripts/setup_ec2.sh \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-api}]" \
  --count 1
```

### 5.3 Verify EC2 Deployment

```bash
# Get instance public IP
export INSTANCE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=${PROJECT_NAME}-api" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

# Test health endpoint
curl http://${INSTANCE_IP}:8000/health

# Test prediction
curl -X POST "http://${INSTANCE_IP}:8000/api/v1/predict?top_k=3" \
  -F "file=@../Data/Clean/Clean\ \(1\).jpeg"
```

---

## Step 6: Deployment Option B — ECS Fargate

### 6.1 Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster \
  --cluster-name ${PROJECT_NAME}-cluster \
  --settings name=containerInsights,value=enabled \
  --region ${AWS_REGION}

# Create CloudWatch log group
aws logs create-log-group \
  --log-group-name /ecs/${PROJECT_NAME} \
  --region ${AWS_REGION}
```

### 6.2 Create Task Definition

```bash
cat <<EOF > ecs-task-definition.json
{
  "family": "${PROJECT_NAME}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-ecs-execution-role",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "${ECR_URI}:v1.0.0",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_PORT", "value": "8000"},
        {"name": "MODEL_PATH", "value": "/app/models/trained_effnet_finetune.keras"},
        {"name": "MODEL_PRELOAD", "value": "true"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${PROJECT_NAME}",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json \
  --region ${AWS_REGION}
```

### 6.3 Create Application Load Balancer

```bash
# Get default VPC
export VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)

# Get subnets
export SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${VPC_ID}" --query 'Subnets[*].SubnetId' --output text | tr '\t' ',')

# Create ALB
export ALB_ARN=$(aws elbv2 create-load-balancer \
  --name ${PROJECT_NAME}-alb \
  --subnets $(echo ${SUBNETS} | tr ',' ' ') \
  --security-groups ${SG_ID} \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# Create target group
export TG_ARN=$(aws elbv2 create-target-group \
  --name ${PROJECT_NAME}-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id ${VPC_ID} \
  --target-type ip \
  --health-check-path /health \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn ${ALB_ARN} \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=${TG_ARN}
```

### 6.4 Create ECS Service with Auto Scaling

```bash
# Create service
aws ecs create-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service-name ${PROJECT_NAME}-service \
  --task-definition ${PROJECT_NAME}:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$(echo ${SUBNETS})],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=${TG_ARN},containerName=api,containerPort=8000" \
  --region ${AWS_REGION}

# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/${PROJECT_NAME}-cluster/${PROJECT_NAME}-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10 \
  --role-arn arn:aws:iam::${ACCOUNT_ID}:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService

# Create scaling policy (CPU)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/${PROJECT_NAME}-cluster/${PROJECT_NAME}-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name ${PROJECT_NAME}-cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "PredefinedMetricSpecification": {"PredefinedMetricType": "ECSServiceAverageCPUUtilization"},
    "TargetValue": 70.0,
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

### 6.5 Verify ECS Deployment

```bash
# Get ALB DNS
export ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns ${ALB_ARN} \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

# Test endpoint
curl http://${ALB_DNS}/health
curl http://${ALB_DNS}/model/info
```

---

## Step 7: Deployment Option C — AWS Lambda

### 7.1 Prepare Lambda Package

```bash
mkdir -p lambda-package
cd lambda-package

# Install dependencies for Lambda layer
pip install \
  tensorflow-cpu==2.16.0 \
  pillow \
  numpy \
  fastapi \
  mangum \
  -t python/lib/python3.11/site-packages \
  --platform manylinux2014_x86_64 \
  --only-binary=:all:

# Create layer zip
zip -r ../lambda-layer.zip python/

# Create function code
cat <<EOF > lambda_function.py
import json
import base64
import boto3
import os
from io import BytesIO
from PIL import Image
import numpy as np
import tensorflow as tf

s3 = boto3.client('s3')
MODEL_BUCKET = os.environ['MODEL_BUCKET']
MODEL_KEY = os.environ['MODEL_KEY']

# Global model (cold start only)
model = None
class_names = ["Bird-drop", "Clean", "Dusty", "Electrical-damage", "Physical-Damage", "Snow-Covered"]

def load_model():
    global model
    if model is None:
        # Download model from S3 to /tmp
        local_path = '/tmp/model.keras'
        s3.download_file(MODEL_BUCKET, MODEL_KEY, local_path)
        model = tf.keras.models.load_model(local_path)
    return model

def preprocess_image(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img = img.resize((224, 224))
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def lambda_handler(event, context):
    try:
        # Parse image from base64
        body = json.loads(event['body'])
        image_bytes = base64.b64decode(body['image'])
        top_k = body.get('top_k', 3)
        
        # Load and predict
        m = load_model()
        img = preprocess_image(image_bytes)
        predictions = m.predict(img, verbose=0)[0]
        
        # Get top-K
        top_indices = np.argsort(predictions)[::-1][:top_k]
        results = [
            {"class": class_names[i], "confidence": float(predictions[i])}
            for i in top_indices
        ]
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'prediction': results[0]['class'],
                'confidence': results[0]['confidence'],
                'top_k': results
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
EOF

zip ../lambda-function.zip lambda_function.py
cd ..
```

### 7.2 Deploy Lambda Function

```bash
# Publish layer
export LAYER_ARN=$(aws lambda publish-layer-version \
  --layer-name ${PROJECT_NAME}-dependencies \
  --description "TensorFlow and dependencies" \
  --zip-file fileb://lambda-layer.zip \
  --compatible-runtimes python3.11 \
  --query 'LayerVersionArn' \
  --output text)

# Create function
aws lambda create-function \
  --function-name ${PROJECT_NAME}-inference \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-function.zip \
  --layers ${LAYER_ARN} \
  --memory-size 3008 \
  --timeout 30 \
  --environment "Variables={MODEL_BUCKET=${PROJECT_NAME}-models-${ACCOUNT_ID},MODEL_KEY=production/trained_effnet_finetune.keras}" \
  --region ${AWS_REGION}
```

### 7.3 Create Function URL (Optional)

```bash
aws lambda create-function-url-config \
  --function-name ${PROJECT_NAME}-inference \
  --auth-type NONE \
  --cors Config='{AllowOrigins="*",AllowMethods="POST",AllowHeaders="content-type"}'
```

---

## Step 8: Deployment Option D — Amazon SageMaker

### 8.1 Create SageMaker Model

```bash
# Upload model to SageMaker default bucket
export SAGEMAKER_BUCKET="sagemaker-${AWS_REGION}-${ACCOUNT_ID}"
aws s3 mb s3://${SAGEMAKER_BUCKET} --region ${AWS_REGION} 2>/dev/null || true

aws s3 cp ../models/trained_effnet_finetune.keras \
  s3://${SAGEMAKER_BUCKET}/${PROJECT_NAME}/model.keras

# Create SageMaker model
aws sagemaker create-model \
  --model-name ${PROJECT_NAME}-model \
  --primary-container '{
    "Image": "763104351884.dkr.ecr.'${AWS_REGION}'.amazonaws.com/tensorflow-inference:2.13-cpu",
    "ModelDataUrl": "s3://'${SAGEMAKER_BUCKET}'/'${PROJECT_NAME}'/model.keras",
    "Environment": {
      "SAGEMAKER_PROGRAM": "inference.py",
      "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code"
    }
  }' \
  --execution-role-arn arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-sagemaker-role \
  --region ${AWS_REGION}
```

### 8.2 Deploy SageMaker Endpoint

```bash
# Create endpoint configuration
aws sagemaker create-endpoint-config \
  --endpoint-config-name ${PROJECT_NAME}-endpoint-config \
  --production-variants '[
    {
      "VariantName": "primary",
      "ModelName": "'${PROJECT_NAME}'-model",
      "InitialInstanceCount": 1,
      "InstanceType": "ml.m5.large",
      "InitialVariantWeight": 1.0
    }
  ]' \
  --region ${AWS_REGION}

# Create endpoint
aws sagemaker create-endpoint \
  --endpoint-name ${PROJECT_NAME}-endpoint \
  --endpoint-config-name ${PROJECT_NAME}-endpoint-config \
  --region ${AWS_REGION}

# Wait for endpoint to be ready
aws sagemaker wait endpoint-in-service \
  --endpoint-name ${PROJECT_NAME}-endpoint \
  --region ${AWS_REGION}
```

### 8.3 Test SageMaker Endpoint

```bash
# Invoke endpoint
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name ${PROJECT_NAME}-endpoint \
  --body fileb://test-image.json \
  --content-type application/json \
  --region ${AWS_REGION} \
  output.json

cat output.json
```

---

## Step 9: API Gateway Integration

### 9.1 Create REST API

```bash
# Create API
export API_ID=$(aws apigateway create-rest-api \
  --name ${PROJECT_NAME}-api \
  --description "Solar Panel Classifier API" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' --output text)

# Get root resource
export ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id ${API_ID} \
  --query 'items[0].id' --output text)

# Create /predict resource
export PREDICT_ID=$(aws apigateway create-resource \
  --rest-api-id ${API_ID} \
  --parent-id ${ROOT_ID} \
  --path-part predict \
  --query 'id' --output text)

# Create POST method
aws apigateway put-method \
  --rest-api-id ${API_ID} \
  --resource-id ${PREDICT_ID} \
  --http-method POST \
  --authorization-type NONE
```

### 9.2 Integrate with ECS/ALB

```bash
aws apigateway put-integration \
  --rest-api-id ${API_ID} \
  --resource-id ${PREDICT_ID} \
  --http-method POST \
  --type HTTP_PROXY \
  --integration-http-method POST \
  --uri http://${ALB_DNS}/api/v1/predict

# Deploy API
aws apigateway create-deployment \
  --rest-api-id ${API_ID} \
  --stage-name prod \
  --description "Production deployment"

# Get invoke URL
echo "API URL: https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/predict"
```

### 9.3 Enable Throttling

```bash
aws apigateway update-stage \
  --rest-api-id ${API_ID} \
  --stage-name prod \
  --patch-operations '[
    {"op": "replace", "path": "/throttling/burstLimit", "value": "1000"},
    {"op": "replace", "path": "/throttling/rateLimit", "value": "500"}
  ]'
```

---

## Step 10: CloudWatch Monitoring

### 10.1 Create Dashboard

```bash
cat <<EOF > dashboard.json
{
  "widgets": [
    {
      "type": "metric",
      "x": 0, "y": 0, "width": 12, "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "${ALB_ARN}"]
        ],
        "period": 60,
        "stat": "Sum",
        "region": "${AWS_REGION}",
        "title": "Request Count"
      }
    },
    {
      "type": "metric",
      "x": 12, "y": 0, "width": 12, "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "${ALB_ARN}"]
        ],
        "period": 60,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "Response Time"
      }
    },
    {
      "type": "metric",
      "x": 0, "y": 6, "width": 12, "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", "ServiceName", "${PROJECT_NAME}-service", "ClusterName", "${PROJECT_NAME}-cluster"]
        ],
        "period": 60,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "ECS CPU Utilization"
      }
    },
    {
      "type": "metric",
      "x": 12, "y": 6, "width": 12, "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ECS", "MemoryUtilization", "ServiceName", "${PROJECT_NAME}-service", "ClusterName", "${PROJECT_NAME}-cluster"]
        ],
        "period": 60,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "ECS Memory Utilization"
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
  --dashboard-name ${PROJECT_NAME}-dashboard \
  --dashboard-body file://dashboard.json
```

### 10.2 Create Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ${PROJECT_NAME}-high-cpu \
  --alarm-description "Alarm when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=${PROJECT_NAME}-service Name=ClusterName,Value=${PROJECT_NAME}-cluster \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:${AWS_REGION}:${ACCOUNT_ID}:alerts-topic

# High latency alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ${PROJECT_NAME}-high-latency \
  --alarm-description "Alarm when latency exceeds 1 second" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 1.0 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=LoadBalancer,Value=${ALB_ARN} \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:${AWS_REGION}:${ACCOUNT_ID}:alerts-topic
```

---

## Step 11: CI/CD with AWS CodePipeline

### 11.1 Create Pipeline

```bash
# Create S3 bucket for artifacts
aws s3 mb s3://${PROJECT_NAME}-pipeline-${ACCOUNT_ID} --region ${AWS_REGION}

# Create CodeBuild project
cat <<EOF > codebuild-project.json
{
  "name": "${PROJECT_NAME}-build",
  "source": {
    "type": "GITHUB",
    "location": "https://github.com/your-org/Classification_CNN_2D.git",
    "buildspec": "buildspec.yml"
  },
  "artifacts": {
    "type": "S3",
    "location": "${PROJECT_NAME}-pipeline-${ACCOUNT_ID}"
  },
  "environment": {
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/standard:7.0",
    "computeType": "BUILD_GENERAL1_MEDIUM",
    "privilegedMode": true
  },
  "serviceRole": "arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-codebuild-role"
}
EOF

aws codebuild create-project --cli-input-json file://codebuild-project.json

# Create pipeline
aws codepipeline create-pipeline --pipeline '{
  "name": "'${PROJECT_NAME}-pipeline'",
  "roleArn": "arn:aws:iam::'${ACCOUNT_ID}':role/'${PROJECT_NAME}'-codepipeline-role",
  "artifactStore": {
    "type": "S3",
    "location": "'${PROJECT_NAME}'-pipeline-'${ACCOUNT_ID}'"
  },
  "stages": [
    {
      "name": "Source",
      "actions": [{
        "name": "Source",
        "actionTypeId": {"category": "Source", "owner": "ThirdParty", "provider": "GitHub", "version": "1"},
        "configuration": {"Owner": "your-org", "Repo": "Classification_CNN_2D", "Branch": "main"},
        "outputArtifacts": [{"name": "SourceCode"}]
      }]
    },
    {
      "name": "Build",
      "actions": [{
        "name": "Build",
        "actionTypeId": {"category": "Build", "owner": "AWS", "provider": "CodeBuild", "version": "1"},
        "configuration": {"ProjectName": "'${PROJECT_NAME}'-build"},
        "inputArtifacts": [{"name": "SourceCode"}],
        "outputArtifacts": [{"name": "BuildOutput"}]
      }]
    },
    {
      "name": "Deploy",
      "actions": [{
        "name": "Deploy",
        "actionTypeId": {"category": "Deploy", "owner": "AWS", "provider": "ECS", "version": "1"},
        "configuration": {"ClusterName": "'${PROJECT_NAME}'-cluster", "ServiceName": "'${PROJECT_NAME}'-service"},
        "inputArtifacts": [{"name": "BuildOutput"}]
      }]
    }
  ]
}'
```

### 11.2 Create buildspec.yml

```bash
cat <<EOF > ../buildspec.yml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
  build:
    commands:
      - echo Build started on \`date\`
      - echo Building the Docker image...
      - docker build -f docker/Dockerfile -t $PROJECT_NAME:latest .
      - docker tag $PROJECT_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME:$CODEBUILD_BUILD_NUMBER
  post_build:
    commands:
      - echo Build completed on \`date\`
      - echo Pushing the Docker image...
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME:$CODEBUILD_BUILD_NUMBER
      - printf '[{"name":"api","imageUri":"%s"}]' $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME:$CODEBUILD_BUILD_NUMBER > imagedefinitions.json
artifacts:
  files: imagedefinitions.json
EOF
```

---

## 💰 Cost Optimization

### Monthly Cost Estimates (us-east-1)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **EC2** | t3.medium × 2 | ~$60 |
| **ECS Fargate** | 1 vCPU, 2 GB × 2 | ~$75 |
| **Lambda** | 3 GB, 1M requests | ~$20 |
| **SageMaker** | ml.m5.large × 1 | ~$120 |
| **ALB** | 1 LB + LCU | ~$22 |
| **S3** | 100 GB Standard | ~$2.30 |
| **CloudWatch** | Logs + Metrics | ~$15 |
| **API Gateway** | 1M requests | ~$3.50 |
| **Data Transfer** | 500 GB outbound | ~$45 |
| **Total (EC2)** | | **~$147** |
| **Total (ECS)** | | **~$162** |
| **Total (Lambda)** | | **~$107** |

### Cost Reduction Strategies

```bash
# 1. Use Spot Instances (60-70% savings)
aws ec2 request-spot-instances \
  --instance-count 2 \
  --launch-specification '{
    "ImageId": "ami-0c02fb55956c7d316",
    "InstanceType": "t3.medium",
    "IamInstanceProfile": {"Name": "'${PROJECT_NAME}'-ec2-profile"}
  }'

# 2. Use Graviton instances (20% cheaper)
# Replace t3.medium with t4g.medium

# 3. S3 Intelligent-Tiering
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket ${PROJECT_NAME}-models-${ACCOUNT_ID} \
  --id default \
  --intelligent-tiering-configuration '{
    "Status": "Enabled",
    "Tierings": [
      {"Days": 90, "AccessTier": "ARCHIVE_ACCESS"},
      {"Days": 180, "AccessTier": "DEEP_ARCHIVE_ACCESS"}
    ]
  }'

# 4. Lambda provisioned concurrency (predictable scaling)
aws lambda put-provisioned-concurrency-config \
  --function-name ${PROJECT_NAME}-inference \
  --qualifier PROD \
  --provisioned-concurrent-executions 5

# 5. SageMaker Serverless (pay per inference)
aws sagemaker create-endpoint-config \
  --endpoint-config-name ${PROJECT_NAME}-serverless-config \
  --production-variants '[{
    "VariantName": "serverless",
    "ModelName": "'${PROJECT_NAME}'-model",
    "ServerlessConfig": {"MemorySizeInMB": 2048, "MaxConcurrency": 10}
  }]'
```

---

## 🔒 Security Best Practices

### Network Security
```bash
# Enable VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids ${VPC_ID} \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/${PROJECT_NAME}-flow-logs

# Enable AWS Shield Advanced (DDoS protection)
aws shield create-protection \
  --name ${PROJECT_NAME}-shield \
  --resource-arn ${ALB_ARN}
```

### Data Encryption
```bash
# Enable S3 default encryption with KMS
aws s3api put-bucket-encryption \
  --bucket ${PROJECT_NAME}-models-${ACCOUNT_ID} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "alias/aws/s3"
      },
      "BucketKeyEnabled": true
    }]
  }'

# Enable ECR image encryption
aws ecr put-registry-scanning-configuration \
  --scan-type ENHANCED
```

### IAM Least Privilege
```bash
# Regularly audit IAM policies
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d > credential-report.csv

# Enable MFA for root account
aws iam create-virtual-mfa-device --virtual-mfa-device-name root-mfa
```

---

## 🐛 Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| ECR login fails | `aws ecr get-login-password` error | Verify IAM permissions: `ecr:GetAuthorizationToken` |
| ECS task stuck PENDING | Insufficient Fargate capacity | Check service events: `aws ecs describe-services` |
| Lambda cold start slow | Model loading takes time | Use provisioned concurrency or EFS for model storage |
| ALB 502 Bad Gateway | Target health check failing | Verify security group allows port 8000 from ALB SG |
| SageMaker endpoint creation fails | IAM role missing S3 access | Attach `AmazonSageMakerFullAccess` or custom S3 policy |
| High CloudWatch costs | Excessive log retention | Set retention to 7 days: `aws logs put-retention-policy` |
| Terraform state lock | Concurrent modifications | Run `terraform force-unlock <LOCK_ID>` |

### Common AWS CLI Commands

```bash
# Check ECS service events
aws ecs describe-services \
  --cluster ${PROJECT_NAME}-cluster \
  --services ${PROJECT_NAME}-service \
  --query 'services[0].events[:5]'

# Check Lambda logs
aws logs tail /aws/lambda/${PROJECT_NAME}-inference --follow

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn ${TG_ARN}

# Force ECS deployment
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --force-new-deployment

# Rollback ECS deployment
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --task-definition ${PROJECT_NAME}:$(($(aws ecs describe-task-definition --task-definition ${PROJECT_NAME} --query 'taskDefinition.revision' --output text) - 1))
```

---

## 📚 Reference

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
