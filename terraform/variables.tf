# Terraform Variables
# ===================

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "solar-panel-classifier"
}

variable "ec2_instance_type" {
  description = "EC2 instance type for API server"
  type        = string
  default     = "t3.medium"
}

variable "ec2_ami" {
  description = "AMI ID for EC2 instances"
  type        = string
  default     = "ami-0c02fb55956c7d316" # Amazon Linux 2023 (us-east-1)
}

variable "key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
  default     = "solar-panel-key"
}

variable "api_instance_count" {
  description = "Number of API instances"
  type        = number
  default     = 2
}

variable "enable_gpu" {
  description = "Enable GPU instances for training"
  type        = bool
  default     = false
}

variable "gpu_instance_type" {
  description = "GPU instance type for training"
  type        = string
  default     = "g4dn.xlarge"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}
