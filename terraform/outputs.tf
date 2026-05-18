# Terraform Outputs
# =================

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for model artifacts"
  value       = aws_s3_bucket.models.id
}

output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "autoscaling_group_name" {
  description = "Name of the API auto scaling group"
  value       = aws_autoscaling_group.api.name
}

output "api_security_group_id" {
  description = "Security group ID for API instances"
  value       = aws_security_group.api.id
}
