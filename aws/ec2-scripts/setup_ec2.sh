#!/bin/bash
# EC2 Instance Bootstrap Script
# =============================
# Run this on a fresh Amazon Linux 2023 EC2 instance

set -e

LOG_FILE="/var/log/solar-panel-setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date)] Starting EC2 bootstrap..."

# System update
dnf update -y

# Install dependencies
dnf install -y docker git curl wget python3 python3-pip

# Start Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install docker-compose
curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install --update
rm -rf awscliv2.zip aws/

# Create app directory
mkdir -p /opt/solar-panel-classifier
cd /opt/solar-panel-classifier

# Download models from S3 (replace with your bucket)
# aws s3 cp s3://your-bucket/models/ ./models/ --recursive

# Create systemd service for the API
cat > /etc/systemd/system/solar-panel-api.service << 'EOF'
[Unit]
Description=Solar Panel Classifier API
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/solar-panel-classifier
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable solar-panel-api

echo "[$(date)] Bootstrap complete. Reboot or start the service with:"
echo "  systemctl start solar-panel-api"
