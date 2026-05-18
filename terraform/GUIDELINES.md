# Terraform Deployment Guidelines

## Solar Panel Classifier — AWS Infrastructure as Code

This document provides step-by-step instructions for deploying the Solar Panel Classifier infrastructure on AWS using Terraform.

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Step-by-Step Deployment](#-step-by-step-deployment)
- [State Management](#-state-management)
- [Post-Deployment](#-post-deployment)
- [CI/CD Integration](#-cicd-integration)
- [Cost Optimization](#-cost-optimization)
- [Troubleshooting](#-troubleshooting)
- [Security Checklist](#-security-checklist)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 INTERNET                                    │
│                                    │                                        │
│                        ┌───────────▼───────────┐                           │
│                        │  Route 53 / DNS       │                           │
│                        │  (yourdomain.com)     │                           │
│                        └───────────┬───────────┘                           │
│                                    │                                        │
│                        ┌───────────▼───────────┐                           │
│                        │  Application LB       │                           │
│                        │  (TLS 1.3, HTTP/2)    │                           │
│                        │  Port: 80, 443        │                           │
│                        └───────────┬───────────┘                           │
│                                    │                                        │
│    ┌───────────────────────────────┼───────────────────────────────┐      │
│    │                               │                               │      │
│    ▼                               ▼                               ▼      │
│ ┌────────┐                   ┌────────┐                   ┌────────┐     │
│ │  EC2   │                   │  EC2   │                   │  EC2   │     │
│ │  AZ-a  │                   │  AZ-b  │                   │  AZ-c  │     │
│ │ API 1  │                   │ API 2  │                   │ API N  │     │
│ │Port:8000│                  │Port:8000│                  │Port:8000│    │
│ └───┬────┘                   └───┬────┘                   └───┬────┘    │
│     │                            │                            │         │
│     └────────────────────────────┼────────────────────────────┘         │
│                                  │                                       │
│                        ┌─────────▼──────────┐                          │
│                        │  EBS / S3 (Models) │                          │
│                        └────────────────────┘                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPORTING SERVICES                                  │
│                                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │    VPC     │  │    ECR     │  │    S3      │  │ CloudWatch │          │
│  │  10.0.0.0  │  │ (Registry) │  │ (Models)   │  │ (Logs)     │          │
│  │   /16      │  │            │  │            │  │            │          │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘          │
│                                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                          │
│  │    IAM     │  │ Auto Scale │  │    SG      │                          │
│  │   Roles    │  │   Group    │  │  (Rules)   │                          │
│  └────────────┘  └────────────┘  └────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Resource Map

| Resource | Purpose | File |
|----------|---------|------|
| VPC | Network isolation | `main.tf` |
| Public Subnets | ALB placement (2 AZs) | `main.tf` |
| Private Subnets | EC2 placement (2 AZs) | `main.tf` |
| Internet Gateway | Public internet access | `main.tf` |
| Application Load Balancer | Traffic distribution | `main.tf` |
| Target Group | Health checks & routing | `main.tf` |
| Auto Scaling Group | Dynamic instance management | `main.tf` |
| Launch Template | Instance configuration | `main.tf` |
| Security Groups | Firewall rules | `main.tf` |
| ECR Repository | Docker image registry | `main.tf` |
| S3 Bucket | Model artifact storage | `main.tf` |
| IAM Role | EC2 permissions | `main.tf` |

---

## 📋 Prerequisites

### Required Tools

```bash
# Install Terraform (v1.5+)
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform version

# Install AWS CLI (v2)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
sudo ./aws/install --update
aws --version

# Install Docker (for image builds)
# See: https://docs.docker.com/engine/install/
```

### AWS Configuration

```bash
# Configure AWS credentials
aws configure
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: us-east-1
# Default output format: json

# Verify credentials
aws sts get-caller-identity
# Expected output: Account, UserId, Arn
```

### Required IAM Permissions

Your AWS user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "autoscaling:*",
        "elasticloadbalancing:*",
        "iam:*",
        "s3:*",
        "ecr:*",
        "logs:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

> ⚠️ In production, scope these permissions to specific resources.

---

## ⚡ Quick Start

```bash
cd Classification_CNN_2D/terraform

# Initialize
terraform init

# Plan
terraform plan -var="environment=production"

# Apply (takes ~5 minutes)
terraform apply -auto-approve -var="environment=production"

# Get outputs
terraform output alb_dns_name
```

---

## 📖 Step-by-Step Deployment

### Step 1: Configure Variables

Review and customize `terraform/variables.tf`:

```bash
cd terraform

# Create a terraform.tfvars file for your environment
cat <<EOF > terraform.tfvars
aws_region         = "us-east-1"
environment        = "production"
project_name       = "solar-panel-classifier"
ec2_instance_type  = "t3.medium"
api_instance_count = 2
key_name           = "your-ec2-keypair-name"
vpc_cidr           = "10.0.0.0/16"
domain_name        = "api.yourdomain.com"
EOF
```

### Step 2: Initialize Terraform Backend

```bash
terraform init
```

This creates:
- Local `.terraform/` directory with provider plugins
- State lock table reference (if S3 backend configured)

### Step 3: Validate Configuration

```bash
terraform validate
```

Expected output:
```
Success! The configuration is valid.
```

### Step 4: Plan the Deployment

```bash
terraform plan -out=tfplan
```

Review the planned changes:
- VPC and subnets
- Security groups
- ALB and target group
- Launch template
- Auto Scaling Group
- S3 bucket
- ECR repository
- IAM roles

### Step 5: Apply the Infrastructure

```bash
terraform apply tfplan
```

Or apply directly:
```bash
terraform apply -auto-approve
```

Expected output after ~5 minutes:
```
Apply complete! Resources: 25 added, 0 changed, 0 destroyed.

Outputs:

alb_dns_name = "solar-panel-classifier-alb-123456789.us-east-1.elb.amazonaws.com"
ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/solar-panel-classifier"
s3_bucket_name = "solar-panel-classifier-models-123456789012"
```

### Step 6: Build and Push Docker Image

```bash
cd ..

# Build image
docker build -f docker/Dockerfile -t solar-panel-classifier:latest .

# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(terraform -chdir=terraform output -raw ecr_repository_url | cut -d'/' -f1)

# Tag image
ECR_URL=$(terraform -chdir=terraform output -raw ecr_repository_url)
docker tag solar-panel-classifier:latest $ECR_URL:latest
docker tag solar-panel-classifier:latest $ECR_URL:v1.0.0

# Push to ECR
docker push $ECR_URL:latest
docker push $ECR_URL:v1.0.0
```

### Step 7: Upload Model Artifacts to S3

```bash
S3_BUCKET=$(terraform -chdir=terraform output -raw s3_bucket_name)

# Upload models
aws s3 sync models/ s3://$S3_BUCKET/production/ \
  --exclude "*.gitkeep" \
  --storage-class INTELLIGENT_TIERING

# Verify
aws s3 ls s3://$S3_BUCKET/production/
```

### Step 8: Update Launch Template with New Image

The Auto Scaling Group uses the latest Launch Template version automatically. To update running instances:

```bash
# Trigger instance refresh
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name $(terraform -chdir=terraform output -raw autoscaling_group_name) \
  --strategy Rolling

# Monitor refresh
aws autoscaling describe-instance-refreshes \
  --auto-scaling-group-name $(terraform -chdir=terraform output -raw autoscaling_group_name)
```

### Step 9: Configure DNS (Route 53)

```bash
# Get ALB DNS name
ALB_DNS=$(terraform -chdir=terraform output -raw alb_dns_name)

# Create Route 53 alias record (replace ZONE_ID and DOMAIN)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.yourdomain.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "'"$ALB_DNS"'",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

### Step 10: Verify Deployment

```bash
# Check EC2 instances
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=solar-panel-classifier-api*" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]'

# Check target group health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names solar-panel-classifier-api-tg \
    --query 'TargetGroups[0].TargetGroupArn' --output text)

# Test endpoint
curl http://$(terraform -chdir=terraform output -raw alb_dns_name)/health
```

---

## 🗄️ State Management

### S3 Remote State (Recommended for Team Use)

```bash
# Create S3 bucket for state
cat <<EOF > backend.tf
terraform {
  backend "s3" {
    bucket         = "solar-panel-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
EOF

# Create bucket and DynamoDB table
aws s3 mb s3://solar-panel-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket solar-panel-terraform-state \
  --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Reinitialize with remote backend
terraform init -migrate-state
```

### State Commands

```bash
# View state
terraform state list

# View specific resource
terraform state show aws_autoscaling_group.api

# Pull state to local
terraform state pull > terraform.tfstate

# Import existing resource
terraform import aws_s3_bucket.models existing-bucket-name
```

---

## ✅ Post-Deployment

### Verify All Outputs

```bash
terraform output
```

| Output | Description | Example |
|--------|-------------|---------|
| `alb_dns_name` | Load balancer URL | `abc.elb.amazonaws.com` |
| `ecr_repository_url` | Docker registry | `123.dkr.ecr.../solar-panel-classifier` |
| `s3_bucket_name` | Model storage | `solar-panel-classifier-models-123` |
| `vpc_id` | VPC identifier | `vpc-0abc123` |
| `autoscaling_group_name` | ASG name | `solar-panel-classifier-api-asg` |

### Access the Application

```bash
# Health check
curl http://$(terraform output -raw alb_dns_name)/health

# API docs (if domain configured)
curl https://api.yourdomain.com/docs

# Predict
curl -X POST "http://$(terraform output -raw alb_dns_name)/api/v1/predict?top_k=3" \
  -F "file=@Data/Clean/Clean\ \(1\).jpeg"
```

---

## 🔁 CI/CD Integration

### GitHub Actions Workflow

Add to `.github/workflows/deploy-aws.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Terraform Init
        run: terraform -chdir=terraform init

      - name: Terraform Plan
        run: terraform -chdir=terraform plan -no-color

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: terraform -chdir=terraform apply -auto-approve

      - name: Build & Push Image
        run: |
          docker build -f docker/Dockerfile -t app:latest .
          aws ecr get-login-password | docker login --username AWS --password-stdin ${{ steps.ecr.outputs.registry }}
          docker tag app:latest ${{ steps.ecr.outputs.registry }}/solar-panel-classifier:${{ github.sha }}
          docker push ${{ steps.ecr.outputs.registry }}/solar-panel-classifier:${{ github.sha }}
```

---

## 💰 Cost Optimization

### Resource Costs (us-east-1, approximate)

| Resource | Specification | Monthly Cost |
|----------|--------------|--------------|
| EC2 (t3.medium) | 2 instances × 730h | ~$60 |
| ALB | 1 × hourly + LCU | ~$20 |
| S3 (Standard) | 100 GB | ~$2.30 |
| Data Transfer | 500 GB outbound | ~$45 |
| CloudWatch | Logs + Metrics | ~$10 |
| **Total** | | **~$140/month** |

### Cost Reduction Strategies

```bash
# Use Spot Instances for non-production
terraform apply -var="ec2_instance_type=t3.medium" -var="environment=staging"

# Use S3 Intelligent-Tiering
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket $(terraform output -raw s3_bucket_name) \
  --id Default \
  --intelligent-tiering-configuration '{"Status": "Enabled", "Tierings": [{"Days": 90, "AccessTier": "ARCHIVE_ACCESS"}]}'

# Right-size instances based on CloudWatch metrics
# Consider Graviton (t4g.medium) for 20% savings
```

---

## 🐛 Troubleshooting

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| `terraform init` fails | Check S3 bucket permissions | Verify AWS credentials and IAM policies |
| EC2 instances not launching | Check ASG activity | `aws autoscaling describe-scaling-activities` |
| Health checks failing | Verify security group rules | Allow port 8000 from ALB security group |
| 503 from ALB | Target group health check path | Verify `/health` endpoint returns 200 |
| Image pull fails | ECR authentication | Run `aws ecr get-login-password` |
| High latency | Insufficient CPU/memory | Scale up instance type or increase replica count |

### Useful Commands

```bash
# Check Terraform state
terraform show

# Check plan for drift
terraform plan -detailed-exitcode

# Taint resource for recreation
terraform taint aws_instance.example

# Destroy everything (WARNING: deletes all resources)
terraform destroy -auto-approve

# Refresh state
terraform refresh
```

---

## 🔒 Security Checklist

- [ ] **S3 Bucket:** Versioning enabled, encryption at rest (AES-256/SSE-KMS)
- [ ] **ECR:** Image scanning enabled, immutable tags
- [ ] **IAM:** Least-privilege roles, no hardcoded credentials
- [ ] **Security Groups:** Minimal required ports, no 0.0.0.0/0 on SSH
- [ ] **ALB:** HTTPS listener with valid TLS certificate
- [ ] **EC2:** Non-root user, no password-based SSH
- [ ] **State:** Remote S3 backend with DynamoDB locking
- [ ] **Secrets:** Stored in AWS Secrets Manager or Parameter Store

### Enable Additional Security

```bash
# Enable VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $(terraform output -raw vpc_id) \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name vpc-flow-logs

# Enable GuardDuty
aws guardduty create-detector --enable

# Enable AWS Config
aws configservice put-configuration-recorder \
  --configuration-recorder name=default \
  --recording-group allSupported=true
```

---

## 📚 Reference

- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Auto Scaling Best Practices](https://docs.aws.amazon.com/autoscaling/ec2/userguide/auto-scaling-benefits.html)
- [Application Load Balancer Guide](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html)
- [ECR Image Scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)
