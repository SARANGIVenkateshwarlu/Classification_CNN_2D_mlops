
# 5. Terraform Infrastructure for AWS

terraform_main = """terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  backend "s3" {
    bucket         = "cnn-mlops-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "cnn-mlops-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "cnn-mlops"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {}

# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  name    = "${var.project_name}-${var.environment}"
  cidr    = var.vpc_cidr
  azs     = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets = [for i in range(3) : cidrsubnet(var.vpc_cidr, 8, i)]
  public_subnets  = [for i in range(3) : cidrsubnet(var.vpc_cidr, 8, i + 3)]
  
  enable_nat_gateway     = true
  single_nat_gateway     = var.environment == "dev"
  enable_dns_hostnames   = true
  enable_dns_support     = true
  
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
  
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  cluster_name    = var.cluster_name
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true
  
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }
  
  # Managed Node Groups
  eks_managed_node_groups = {
    general = {
      desired_size = var.environment == "prod" ? 3 : 2
      min_size     = var.environment == "prod" ? 2 : 1
      max_size     = var.environment == "prod" ? 10 : 5
      
      instance_types = ["m6i.xlarge"]
      capacity_type  = var.environment == "prod" ? "ON_DEMAND" : "SPOT"
      
      labels = {
        workload = "general"
      }
      
      update_config = {
        max_unavailable_percentage = 25
      }
    }
    
    gpu = {
      desired_size = var.environment == "prod" ? 1 : 0
      min_size     = 0
      max_size     = 3
      
      instance_types = ["g4dn.xlarge"]
      ami_type       = "AL2_x86_64_GPU"
      
      labels = {
        workload = "gpu-training"
        nvidia.com/gpu = "true"
      }
      
      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
  }
  
  # IRSA for service accounts
  enable_irsa = true
}

# S3 Buckets
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "models" {
  bucket = "${var.project_name}-models-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_lifecycle_configuration" "models" {
  bucket = aws_s3_bucket.models.id
  rule {
    id     = "transition-old-versions"
    status = "Enabled"
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# ECR Repositories
resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.environment == "dev"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "streamlit" {
  name                 = "${var.project_name}-streamlit"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.environment == "dev"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "training" {
  name                 = "${var.project_name}-training"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.environment == "dev"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

# RDS for MLflow Metadata
resource "aws_db_subnet_group" "mlflow" {
  name       = "${var.project_name}-mlflow-${var.environment}"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "mlflow" {
  identifier           = "${var.project_name}-mlflow-${var.environment}"
  engine              = "postgres"
  engine_version      = "14.9"
  instance_class      = var.environment == "prod" ? "db.t3.medium" : "db.t3.micro"
  allocated_storage   = 20
  storage_type        = "gp2"
  
  db_name  = "mlflow"
  username = "mlflow"
  password = random_password.mlflow.result
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.mlflow.name
  
  skip_final_snapshot = var.environment == "dev"
  
  backup_retention_period = var.environment == "prod" ? 7 : 1
}

resource "random_password" "mlflow" {
  length  = 16
  special = true
}

# Secrets Manager
resource "aws_secretsmanager_secret" "mlflow_db" {
  name = "${var.project_name}/mlflow-db-${var.environment}"
}

resource "aws_secretsmanager_secret_version" "mlflow_db" {
  secret_id = aws_secretsmanager_secret.mlflow_db.id
  secret_string = jsonencode({
    username = aws_db_instance.mlflow.username
    password = aws_db_instance.mlflow.password
    host     = aws_db_instance.mlflow.address
    port     = aws_db_instance.mlflow.port
    dbname   = aws_db_instance.mlflow.db_name
  })
}

# IAM Role for Service Account (IRSA)
resource "aws_iam_role" "cnn_mlops" {
  name = "${var.project_name}-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = module.eks.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${module.eks.oidc_provider}:sub" = "system:serviceaccount:cnn-mlops:cnn-mlops-sa"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "cnn_mlops" {
  name = "${var.project_name}-policy-${var.environment}"
  role = aws_iam_role.cnn_mlops.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*",
          aws_s3_bucket.models.arn,
          "${aws_s3_bucket.models.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.mlflow_db.arn
      }
    ]
  })
}

# Outputs
output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "s3_data_bucket" {
  description = "S3 bucket for data"
  value       = aws_s3_bucket.data_lake.bucket
}

output "s3_models_bucket" {
  description = "S3 bucket for models"
  value       = aws_s3_bucket.models.bucket
}

output "mlflow_db_endpoint" {
  description = "MLflow database endpoint"
  value       = aws_db_instance.mlflow.address
  sensitive   = true
}
"""

terraform_variables = """variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "cnn-mlops"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "cnn-mlops-cluster"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}
"""

terraform_outputs = """output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "ecr_api_repository_url" {
  description = "ECR repository URL for API"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_streamlit_repository_url" {
  description = "ECR repository URL for Streamlit"
  value       = aws_ecr_repository.streamlit.repository_url
}

output "irsa_role_arn" {
  description = "IAM role ARN for service account"
  value       = aws_iam_role.cnn_mlops.arn
}
"""

# Write files
with open(f"{project_root}/terraform/main.tf", "w") as f:
    f.write(terraform_main)

with open(f"{project_root}/terraform/variables.tf", "w") as f:
    f.write(terraform_variables)

with open(f"{project_root}/terraform/outputs.tf", "w") as f:
    f.write(terraform_outputs)

print("✅ Terraform infrastructure files created")
