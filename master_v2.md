# Master Guide V2: From Zero to Production

## A Senior Engineer's Step-by-Step Guide for First-Time Cloud Deployers

> **Hey there!** Think of this guide like learning to drive. You don't need to know how the engine works on day one. You just need to know: (1) how to start the car, (2) how to steer, and (3) how to park. We'll build up from there. Every section assumes you've never touched this tool before.

---

## 📚 Table of Contents

1. [The Big Picture: How Everything Connects](#1-the-big-picture-how-everything-connects)
2. [Component 1: The Model (Your Brain)](#2-component-1-the-model-your-brain)
3. [Component 2: Docker (The Shipping Container)](#3-component-2-docker-the-shipping-container)
4. [Component 3: AWS IAM (The Security Guard)](#4-component-3-aws-iam-the-security-guard)
5. [Component 4: AWS EC2 (The Computer in the Cloud)](#5-component-4-aws-ec2-the-computer-in-the-cloud)
6. [Component 5: Terraform (The Blueprint Maker)](#6-component-5-terraform-the-blueprint-maker)
7. [Component 6: CI/CD (The Robot Assistant)](#7-component-6-cicd-the-robot-assistant)
8. [Integration Lab: Your First End-to-End Deployment](#8-integration-lab-your-first-end-to-end-deployment)
9. [Testing Checklist](#9-testing-checklist)
10. [Troubleshooting for Beginners](#10-troubleshooting-for-beginners)

---

## 1. The Big Picture: How Everything Connects

### The Analogy: Building a Pizza Shop

Imagine you're opening a pizza shop. Here's how the tech maps to the real world:

| Tech | Pizza Shop Analogy | What It Actually Does |
|------|-------------------|----------------------|
| **Model** | The chef's recipe | Your trained AI that recognizes solar panel conditions |
| **Docker** | The delivery box | Packages your app so it runs the same everywhere |
| **AWS EC2** | The rented kitchen | A computer in Amazon's data center running your app |
| **AWS IAM** | The key system | Controls who can enter the kitchen and use the stove |
| **Terraform** | The architect's blueprint | Writes down exactly what kitchen you want, so you can rebuild it anytime |
| **CI/CD** | The auto-pilot robot | Automatically builds, tests, and delivers your pizza when you update the recipe |
| **S3** | The storage room | Keeps your recipes and ingredients safe |
| **ECR** | The labeled fridge | Stores your packaged delivery boxes (Docker images) |

### The Flow (Simple Version)

```
You write code → Docker packages it → Terraform builds the server → 
IAM gives permissions → EC2 runs the app → Model makes predictions → 
CI/CD does this automatically on every update
```

---

## 2. Component 1: The Model (Your Brain)

### What Is It?

The model is a file (like `trained_effnet_finetune.keras`) that contains everything your AI learned during training. Think of it like a chef's brain after culinary school — it knows what "Clean" vs "Dusty" solar panels look like.

### Where Is It?

```
Classification_CNN_2D/
└── models/
    ├── trained_effnet_finetune.keras   ← Our best model (~19 MB)
    ├── trained_effnet_finetune.h5      ← Same thing, older format
    ├── mobilenetv2_2.keras             ← Faster but less accurate
    └── mobilenetv2_2.h5
```

### How to Test It (Without Any Cloud Stuff)

**Step 2.1: Make sure Python environment is ready**

```bash
# Open your terminal (Git Bash on Windows, Terminal on Mac/Linux)
# Navigate to the project folder
cd Classification_CNN_2D

# Activate your virtual environment (the box that holds your Python tools)
source .venv/Scripts/activate    # Windows
# OR
source .venv/bin/activate        # Mac/Linux

# You should see (.venv) at the start of your prompt
```

**Step 2.2: Run a quick prediction test**

```bash
# Use the CLI tool to test the model
python main.py predict --image Data/Clean/Clean\ \(1\).jpeg --top-k 3
```

**What you should see:**
```
Predicting: Data/Clean/Clean (1).jpeg
----------------------------------------
  1. Clean                98.57% ###################
  2. Bird-drop            0.61%
  3. Dusty                0.57%
----------------------------------------
Result: Clean (98.57%)
```

**If this works, your model is healthy!** This is the foundation everything else builds on.

---

## 3. Component 2: Docker (The Shipping Container)

### What Is Docker? (The Shipping Container Analogy)

Imagine you have a machine that makes pizzas. It works perfectly in your kitchen. But when you move it to a friend's kitchen, it breaks because they have a different oven, different electricity, different everything.

**Docker solves this.** It packages your entire kitchen — oven, ingredients, recipes, even the chef — into a standardized shipping container. Now you can move that container anywhere, and it works exactly the same.

In tech terms: Docker packages your Python app, TensorFlow, and all dependencies into one file called an **image**. This image runs the same on your laptop, on a test server, or on Amazon's cloud.

### Key Terms (Don't Skip This)

| Term | Simple Meaning | Pizza Analogy |
|------|---------------|---------------|
| **Dockerfile** | Recipe for building the image | The instructions for packing the kitchen |
| **Image** | The packaged app | The sealed shipping container |
| **Container** | A running instance of the image | The container opened and running in a new location |
| **Registry** | Storage for images | A warehouse that stores containers |

### Step-by-Step: Build and Test Your First Docker Image

**Step 3.1: Install Docker**

```bash
# Check if Docker is installed
docker --version

# If you see something like "Docker version 24.0.7", you're good!
# If not, download from: https://docs.docker.com/get-docker/
```

**Step 3.2: Build the image (this takes 5-10 minutes the first time)**

```bash
# Make sure you're in the project root folder
cd Classification_CNN_2D

# Build the image
docker build -f docker/Dockerfile -t solar-panel-classifier:latest .

# What this means:
# docker         = the tool
# build          = create an image
# -f docker/Dockerfile  = use this recipe file
# -t solar-panel-classifier:latest  = name it "solar-panel-classifier" with tag "latest"
# .              = use the current folder as context
```

**What happens during the build:**
1. Docker downloads a base Linux image (~100 MB)
2. Installs Python and your dependencies (~2 GB)
3. Copies your code into the image
4. Packages everything into one file

**Step 3.3: Verify the image was created**

```bash
docker images

# You should see:
# REPOSITORY                TAG       IMAGE ID       CREATED         SIZE
# solar-panel-classifier    latest    abc123...      2 minutes ago   3.2GB
```

**Step 3.4: Run the container locally (test it!)**

```bash
# Run the container, mapping port 8000 on your machine to port 8000 in the container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models:ro \
  -e MODEL_PATH=/app/models/trained_effnet_finetune.keras \
  --name my-first-container \
  solar-panel-classifier:latest

# What this means:
# run            = start a container
# -d             = run in background (detached)
# -p 8000:8000   = map host port 8000 to container port 8000
# -v ...         = mount your local models folder into the container (read-only)
# -e ...         = set environment variable
# --name ...     = give it a friendly name
# solar-panel-classifier:latest = which image to use
```

**Step 3.5: Test the running container**

```bash
# Check if it's running
docker ps

# You should see "my-first-container" in the list

# Test the health endpoint
curl http://localhost:8000/health

# Expected: {"status":"healthy","model_loaded":true,...}

# Test a prediction
curl -X POST "http://localhost:8000/api/v1/predict?top_k=3" \
  -F "file=@Data/Clean/Clean\ \(1\).jpeg"

# Expected: JSON with prediction results
```

**Step 3.6: Stop and clean up**

```bash
# Stop the container
docker stop my-first-container

# Remove it
docker rm my-first-container

# If you want to free up disk space:
docker system prune -f
```

**🎉 Congratulations! You just containerized your first ML app.**

---

## 4. Component 3: AWS IAM (The Security Guard)

### What Is IAM? (The Building Security Analogy)

Imagine you rent an office building. You need:
- **Keys** for employees to enter
- **Access cards** for different floors
- **A log** of who entered when

**AWS IAM (Identity and Access Management)** does exactly this for cloud resources. It answers three questions:
1. **Who are you?** (Identity = User/Role)
2. **What can you do?** (Access = Permissions)
3. **Where can you do it?** (Scope = Resources)

### Key Terms

| Term | Simple Meaning | Analogy |
|------|---------------|---------|
| **User** | A person who logs in | An employee |
| **Role** | An identity for services | A job title (e.g., "Security Guard") |
| **Policy** | A document listing permissions | A job description |
| **Group** | A collection of users | A department |

### Step-by-Step: Set Up Your First IAM User

**Step 4.1: Log into AWS Console**

1. Go to https://aws.amazon.com/console/
2. Sign in with your root email (the email you used to create AWS)
3. In the search bar at the top, type "IAM" and click it

**Step 4.2: Create an IAM User (NEVER use your root account for daily work!)**

```bash
# We'll use AWS CLI for this (faster and more repeatable)

# Create the user
aws iam create-user --user-name solar-panel-developer

# Attach basic permissions (this is like giving the employee a basic ID card)
aws iam attach-user-policy \
  --user-name solar-panel-developer \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

aws iam attach-user-policy \
  --user-name solar-panel-developer \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-user-policy \
  --user-name solar-panel-developer \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
```

**Step 4.3: Create access keys (like a username/password for programs)**

```bash
aws iam create-access-key --user-name solar-panel-developer

# SAVE THE OUTPUT! It looks like:
# {
#   "AccessKey": {
#     "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
#     "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
#   }
# }
```

**⚠️ CRITICAL: Save these somewhere secure (password manager). You cannot see the Secret Access Key again.**

**Step 4.4: Configure your computer to use these credentials**

```bash
aws configure

# AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name [None]: us-east-1
# Default output format [None]: json
```

**Step 4.5: Verify it works**

```bash
aws sts get-caller-identity

# Expected:
# {
#   "UserId": "AIDACKCEVSQ6C2EXAMPLE",
#   "Account": "123456789012",
#   "Arn": "arn:aws:iam::123456789012:user/solar-panel-developer"
# }
```

**🎉 You now have secure access to AWS!**

---

## 5. Component 4: AWS EC2 (The Computer in the Cloud)

### What Is EC2? (The Rental Car Analogy)

**EC2 = Elastic Compute Cloud**

Imagine you need a computer, but you don't want to buy one. Instead, you rent one from Amazon by the hour. You can:
- Choose the size (small laptop vs powerful workstation)
- Choose the location (data center in Virginia, Ohio, etc.)
- Turn it on when you need it, off when you don't
- Access it from anywhere in the world

That's EC2. It's a virtual computer you rent from Amazon.

### Key Terms

| Term | Simple Meaning | Analogy |
|------|---------------|---------|
| **Instance** | A running virtual computer | A rental car you've picked up |
| **AMI** | The operating system image | The car model (Toyota, Honda) |
| **Instance Type** | The computer's power | Engine size (t3.small = compact, t3.large = SUV) |
| **Security Group** | Firewall rules | The car's lock system |
| **Key Pair** | SSH login credentials | The car keys |
| **EBS** | Hard disk storage | The car's trunk |

### Step-by-Step: Launch Your First EC2 Instance

**Step 5.1: Create a Key Pair (your car keys)**

```bash
# Create a key pair
aws ec2 create-key-pair \
  --key-name solar-panel-key \
  --query 'KeyMaterial' \
  --output text > solar-panel-key.pem

# Secure the key file (Linux/Mac)
chmod 400 solar-panel-key.pem

# On Windows, right-click the file → Properties → Security → Advanced → Disable inheritance → Remove all permissions → Add yourself with Read only
```

**Step 5.2: Create a Security Group (firewall rules)**

```bash
# Get your default VPC ID
export VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --query 'Vpcs[0].VpcId' \
  --output text)

echo "Your VPC ID is: $VPC_ID"

# Create security group
export SG_ID=$(aws ec2 create-security-group \
  --group-name solar-panel-sg \
  --description "Security group for testing solar panel classifier" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

echo "Your Security Group ID is: $SG_ID"

# Allow HTTP (port 80) from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow your app port (8000) from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

# Allow SSH (port 22) from YOUR IP only (safer!)
export MY_IP=$(curl -s https://checkip.amazonaws.com)
echo "Your IP is: $MY_IP"

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr $MY_IP/32
```

**Step 5.3: Launch the instance**

```bash
# Launch a t3.medium instance (2 CPU, 4 GB RAM) with Amazon Linux 2023
export INSTANCE_ID=$(aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name solar-panel-key \
  --security-group-ids $SG_ID \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=solar-panel-test}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Your Instance ID is: $INSTANCE_ID"
```

**Step 5.4: Wait for it to be ready**

```bash
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

echo "Instance is running!"

# Get the public IP
export PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Your instance IP is: $PUBLIC_IP"
```

**Step 5.5: Connect to your instance**

```bash
# SSH into the instance (Linux/Mac)
ssh -i solar-panel-key.pem ec2-user@$PUBLIC_IP

# On Windows, use PuTTY or Git Bash with the same command
# First time? Type "yes" when it asks about host authenticity
```

**What you should see:**
```
   ,     #_
   ~\_  ####_        Amazon Linux 2023
  ~~  \_ #####\
  ~~     \ ###|
  ~~       \#/ ___   https://aws.amazon.com/linux/amazon-linux-2023
   ~~       V~' '->
    ~~~         /
      ~~._.   _/
         _/ _/
       _/m/'
[ec2-user@ip-172-31-XX-XX ~]$
```

**Step 5.6: Install Docker on the instance**

```bash
# Run these commands INSIDE the EC2 instance (after SSH)

# Update the system
sudo dnf update -y

# Install Docker
sudo dnf install -y docker

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to the docker group (so you don't need sudo every time)
sudo usermod -aG docker ec2-user

# Exit and reconnect for group changes to take effect
exit

# Reconnect
ssh -i solar-panel-key.pem ec2-user@$PUBLIC_IP

# Test Docker
docker --version
# Expected: Docker version 24.x.x
```

**Step 5.7: Copy your app to the instance**

On your LOCAL machine (open a new terminal):

```bash
# Create a zip of your project
cd Classification_CNN_2D
zip -r ../solar-panel-app.zip . -x ".venv/*" "Data/*" "kt_dir/*" ".git/*" "__pycache__/*"

# Copy to EC2
scp -i solar-panel-key.pem ../solar-panel-app.zip ec2-user@$PUBLIC_IP:/home/ec2-user/

# Also copy the models separately
scp -i solar-panel-key.pem -r models/ ec2-user@$PUBLIC_IP:/home/ec2-user/
```

Back on the EC2 instance:

```bash
# Unzip the app
cd /home/ec2-user
unzip -q solar-panel-app.zip

# Verify files are there
ls
# You should see: app.py, docker/, models/, requirements.txt, etc.
```

**Step 5.8: Build and run on EC2**

```bash
cd /home/ec2-user

# Build the Docker image (this takes 10-15 minutes on first run)
docker build -f docker/Dockerfile -t solar-panel-classifier:latest .

# Run it
docker run -d \
  -p 8000:8000 \
  -v /home/ec2-user/models:/app/models:ro \
  -e MODEL_PATH=/app/models/trained_effnet_finetune.keras \
  --name solar-panel-api \
  solar-panel-classifier:latest

# Check if it's running
docker ps

# View logs
docker logs -f solar-panel-api
```

**Step 5.9: Test from your local machine**

```bash
# On your LOCAL machine
curl http://$PUBLIC_IP:8000/health

# Expected: {"status":"healthy",...}

# Test a prediction
curl -X POST "http://$PUBLIC_IP:8000/api/v1/predict?top_k=3" \
  -F "file=@Data/Clean/Clean\ \(1\).jpeg"
```

**🎉 Your app is running on a real cloud server!**

**Step 5.10: Clean up (so you don't get charged)**

```bash
# IMPORTANT: Terminate the instance when done testing!
aws ec2 terminate-instances --instance-ids $INSTANCE_ID

# Or in the AWS Console: EC2 → Instances → Select instance → Actions → Instance State → Terminate
```

**AWS charges by the hour. A t3.medium costs about $0.04/hour. Always terminate test instances when done!**

---

## 6. Component 5: Terraform (The Blueprint Maker)

### What Is Terraform? (The Architect Analogy)

Imagine you're building a house. You could:
- **Option A:** Hire workers, tell them verbally what to build, hope they remember everything
- **Option B:** Give them a detailed blueprint they can follow exactly, and reuse for future houses

**Terraform is Option B.** It's a tool that lets you write down exactly what AWS resources you want (in code), and then it creates them for you. The best part? If you make a mistake, you can destroy everything and rebuild it in minutes.

### Key Terms

| Term | Simple Meaning | Analogy |
|------|---------------|---------|
| **Configuration** | Your blueprint file | `main.tf` |
| **State** | Terraform's memory of what it built | `terraform.tfstate` |
| **Plan** | Preview of changes before applying | "Here's what I'm about to build" |
| **Apply** | Actually create the resources | "Build it now" |
| **Destroy** | Delete everything | "Demolish the house" |

### Step-by-Step: Your First Terraform Deployment

**Step 6.1: Install Terraform**

```bash
# Check if installed
terraform --version

# If not, download:
# Windows: https://developer.hashicorp.com/terraform/install
# Mac: brew install terraform
# Linux:
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**Step 6.2: Understand our Terraform files**

```
terraform/
├── providers.tf      ← "I want to use AWS"
├── variables.tf      ← "These are my settings"
├── main.tf           ← "Build these resources"
├── outputs.tf        ← "Show me these results after"
└── user_data.sh      ← "Run this script on new servers"
```

**Step 6.3: Initialize Terraform**

```bash
cd Classification_CNN_2D/terraform

# This downloads the AWS plugin (like installing a driver)
terraform init

# Expected output:
# Initializing the backend...
# Initializing provider plugins...
# - Finding hashicorp/aws versions matching "~> 5.0"...
# - Installing hashicorp/aws v5.x.x...
```

**Step 6.4: Preview what Terraform will build**

```bash
terraform plan

# This shows you EXACTLY what will be created, changed, or destroyed
# It's like an architect showing you the blueprint before construction
# READ THIS CAREFULLY before proceeding
```

**What you should see:**
```
Terraform will perform the following actions:

  # aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + cidr_block           = "10.0.0.0/16"
      ...
    }

  # aws_subnet.public[0] will be created
  + resource "aws_subnet" "public" {
      + cidr_block = "10.0.1.0/24"
      ...
    }

Plan: 25 to add, 0 to change, 0 to destroy.
```

**Step 6.5: Build everything**

```bash
# This actually creates the resources (takes ~5 minutes)
terraform apply -auto-approve

# What happens:
# 1. Creates VPC (network)
# 2. Creates subnets (network zones)
# 3. Creates security groups (firewall)
# 4. Creates ALB (load balancer)
# 5. Creates launch template (server template)
# 6. Creates auto scaling group (auto-managed servers)
# 7. Creates S3 bucket (storage)
# 8. Creates ECR repository (container storage)
```

**Step 6.6: See what was created**

```bash
terraform output

# Shows:
# alb_dns_name = "solar-panel-classifier-alb-123456789.us-east-1.elb.amazonaws.com"
# ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/solar-panel-classifier"
# s3_bucket_name = "solar-panel-classifier-models-123456789012"
```

**Step 6.7: Test the deployment**

```bash
# Get the load balancer URL
export ALB_URL=$(terraform output -raw alb_dns_name)
echo "Your app URL: http://$ALB_URL"

# Test it
curl http://$ALB_URL/health
```

**Step 6.8: Destroy everything (clean up!)**

```bash
# This deletes ALL resources Terraform created
terraform destroy -auto-approve

# IMPORTANT: This is the magic of Terraform.
# Instead of manually deleting 25 resources one by one,
# one command cleans up everything.
```

**🎉 You just built and destroyed a full cloud infrastructure!**

---

## 7. Component 6: CI/CD (The Robot Assistant)

### What Is CI/CD? (The Factory Analogy)

**CI = Continuous Integration**
**CD = Continuous Deployment**

Imagine a factory that makes cars:
- A worker changes the steering wheel design
- The factory automatically: tests the new wheel, checks it fits, builds the car, and delivers it
- No human needed in between

**CI/CD does this for code.** When you push code to GitHub:
1. **CI:** Automatically tests your code, checks formatting, runs security scans
2. **CD:** If tests pass, automatically builds the Docker image and deploys it

### Our CI/CD Pipeline (GitHub Actions)

```
You push code to GitHub
        ↓
GitHub Actions wakes up
        ↓
Stage 1: Code Quality (Black, Flake8, MyPy)
        ↓
Stage 2: Tests (pytest)
        ↓
Stage 3: Security Scan (Bandit)
        ↓
Stage 4: Docker Build
        ↓
Stage 5: Push to ECR (if on main branch)
        ↓
Stage 6: Deploy to ECS/EC2
```

### Step-by-Step: See CI/CD in Action

**Step 7.1: Make a small change**

```bash
# Edit a file (add a comment to main.py)
echo "# Test change for CI/CD" >> main.py

# Commit and push
git add main.py
git commit -m "Test CI/CD pipeline"
git push origin main
```

**Step 7.2: Watch the magic happen**

1. Go to https://github.com/your-username/Classification_CNN_2D/actions
2. You should see a workflow running
3. Click on it to see real-time logs
4. Each step turns green (pass) or red (fail)

**Step 7.3: Understand the workflow file**

Open `.github/workflows/ci-cd.yml`:

```yaml
name: Solar Panel Classifier CI/CD

on:
  push:
    branches: [main, develop]   # Run when code is pushed to these branches

jobs:
  code-quality:                 # Job 1: Check code formatting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4    # Download your code
      - uses: actions/setup-python@v5 # Install Python
      - run: pip install black flake8 mypy
      - run: black --check src/       # Check formatting
      - run: flake8 src/              # Check style
      - run: mypy src/                # Check types

  testing:                      # Job 2: Run tests
    runs-on: ubuntu-latest
    needs: code-quality         # Only run if code-quality passed
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt pytest
      - run: pytest tests/ -v        # Run all tests

  docker-build:                 # Job 3: Build Docker image
    runs-on: ubuntu-latest
    needs: testing              # Only run if tests passed
    steps:
      - uses: actions/checkout@v4
      - run: docker build -f docker/Dockerfile -t app:latest .
```

**🎉 Every time you push code, a robot tests and builds it for you!**

---

## 8. Integration Lab: Your First End-to-End Deployment

### The Mission

Deploy the Solar Panel Classifier to AWS using Terraform, with a Docker container, and verify it works end-to-end.

### Prerequisites Checklist

Before starting, verify you have:
- [ ] AWS account created
- [ ] AWS CLI installed and configured (`aws configure` done)
- [ ] Terraform installed (`terraform --version` works)
- [ ] Docker installed (`docker --version` works)
- [ ] Model files in `models/` folder
- [ ] This repository cloned to your computer

### The 10-Step Integration

**Step 1: Set environment variables**

```bash
export PROJECT_NAME=solar-panel-classifier
export AWS_REGION=us-east-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Project: $PROJECT_NAME"
echo "Region: $AWS_REGION"
echo "Account: $ACCOUNT_ID"
```

**Step 2: Build Docker image locally**

```bash
cd Classification_CNN_2D

# Build
docker build -f docker/Dockerfile -t $PROJECT_NAME:latest .

# Test locally
docker run -d -p 8000:8000 -v $(pwd)/models:/app/models:ro \
  -e MODEL_PATH=/app/models/trained_effnet_finetune.keras \
  --name test-local $PROJECT_NAME:latest

# Verify
curl http://localhost:8000/health

# Stop local test
docker stop test-local && docker rm test-local
```

**Step 3: Create ECR repository**

```bash
aws ecr create-repository --repository-name $PROJECT_NAME --region $AWS_REGION

export ECR_URI=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME
```

**Step 4: Push Docker image to ECR**

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URI

# Tag
docker tag $PROJECT_NAME:latest $ECR_URI:v1.0.0

# Push
docker push $ECR_URI:v1.0.0
```

**Step 5: Upload model to S3**

```bash
aws s3 mb s3://$PROJECT_NAME-models-$ACCOUNT_ID --region $AWS_REGION

aws s3 sync models/ s3://$PROJECT_NAME-models-$ACCOUNT_ID/production/ \
  --exclude "*.gitkeep"
```

**Step 6: Deploy infrastructure with Terraform**

```bash
cd terraform

terraform init
terraform plan -var="environment=production"
terraform apply -auto-approve -var="environment=production"

# Save outputs
export ALB_DNS=$(terraform output -raw alb_dns_name)
export ECR_URL=$(terraform output -raw ecr_repository_url)
export S3_BUCKET=$(terraform output -raw s3_bucket_name)

echo "ALB: http://$ALB_DNS"
```

**Step 7: Update EC2 instances to use your image**

The Terraform creates an Auto Scaling Group. The instances use the `user_data.sh` script to pull and run your image. But first, we need to update the launch template to use your specific ECR image.

```bash
# Get the launch template ID
export LT_ID=$(aws ec2 describe-launch-templates \
  --filters "Name=launch-template-name,Values=solar-panel-classifier-api-*" \
  --query 'LaunchTemplates[0].LaunchTemplateId' \
  --output text)

# Create new version with your image
aws ec2 create-launch-template-version \
  --launch-template-id $LT_ID \
  --source-version '$Latest' \
  --launch-template-data "{
    \"UserData\": \"$(base64 -w 0 <<EOF
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Pull and run
docker pull $ECR_URI:v1.0.0
docker run -d -p 8000:8000 \
  -e MODEL_PATH=/app/models/trained_effnet_finetune.keras \
  -e MODEL_PRELOAD=true \
  --name api $ECR_URI:v1.0.0
EOF
)\"
  }"

# Trigger instance refresh
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name solar-panel-classifier-api-asg \
  --strategy Rolling
```

**Step 8: Wait and verify**

```bash
# Wait for instances to be ready (takes 3-5 minutes)
echo "Waiting for instances..."
sleep 180

# Test health endpoint
curl http://$ALB_DNS/health

# Test prediction
curl -X POST "http://$ALB_DNS/api/v1/predict?top_k=3" \
  -F "file=@../Data/Clean/Clean\ \(1\).jpeg"
```

**Step 9: Test auto-scaling**

```bash
# Generate load to trigger scaling
for i in {1..100}; do
  curl -s -o /dev/null -w "%{http_code}" http://$ALB_DNS/health &
done
wait

# Check if more instances launched
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name solar-panel-classifier-api-asg
```

**Step 10: Clean up**

```bash
# Destroy everything
cd ../terraform
terraform destroy -auto-approve

# Delete ECR images
aws ecr batch-delete-image \
  --repository-name $PROJECT_NAME \
  --image-ids imageTag=v1.0.0

# Empty and delete S3 bucket
aws s3 rm s3://$PROJECT_NAME-models-$ACCOUNT_ID --recursive
aws s3 rb s3://$PROJECT_NAME-models-$ACCOUNT_ID
```

**🎉🎉🎉 YOU DID IT! You deployed a full ML application to AWS! 🎉🎉🎉**

---

## 9. Testing Checklist

### Component Tests

| Component | Test Command | Expected Result |
|-----------|-------------|-----------------|
| Model | `python main.py predict --image Data/Clean/Clean\ \(1\).jpeg` | Shows prediction with confidence |
| Docker Build | `docker build -f docker/Dockerfile -t test:latest .` | Image created successfully |
| Docker Run | `docker run -d -p 8000:8000 -v $(pwd)/models:/app/models:ro test:latest` | Container running |
| Local API | `curl http://localhost:8000/health` | `{"status":"healthy"}` |
| AWS IAM | `aws sts get-caller-identity` | Shows your account info |
| Terraform Plan | `terraform plan` | Shows 25 resources to create |
| Terraform Apply | `terraform apply -auto-approve` | All resources created |
| ALB Health | `curl http://$ALB_DNS/health` | `{"status":"healthy"}` |
| ALB Predict | `curl -X POST "http://$ALB_DNS/api/v1/predict" -F "file=@image.jpg"` | Prediction JSON |
| CI/CD | Push code to GitHub | Actions workflow runs successfully |

### Integration Tests

| Test | How To | Pass Criteria |
|------|--------|---------------|
| End-to-end inference | Upload image → Get prediction | Correct class with >80% confidence |
| Auto-scaling | Generate 100 concurrent requests | HPA scales to >3 pods/instances |
| Rolling update | Deploy new version | Zero downtime (health checks pass) |
| Recovery | Kill one instance | ASG replaces it within 2 minutes |

---

## 10. Troubleshooting for Beginners

### "It doesn't work" — The Universal Fix

When something breaks, check these in order:

**1. Is the service running?**
```bash
# Docker
docker ps

# EC2
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"

# ECS
aws ecs describe-services --cluster $PROJECT_NAME-cluster --services $PROJECT_NAME-service

# Check logs — this is where the answer usually is!
docker logs container-name
aws logs tail /ecs/$PROJECT_NAME --follow
```

**2. Is the port open?**
```bash
# Test locally
curl http://localhost:8000/health

# Test from another machine
curl http://$PUBLIC_IP:8000/health

# If local works but remote doesn't: Security Group is blocking it
```

**3. Are the environment variables set?**
```bash
# Inside container
docker exec container-name env | grep MODEL

# Should show MODEL_PATH=/app/models/...
```

**4. Is the model file there?**
```bash
# Inside container
docker exec container-name ls -la /app/models/

# Should show trained_effnet_finetune.keras
```

### Common Errors and Fixes

| Error | What It Means | How To Fix |
|-------|--------------|-----------|
| `Permission denied` | You don't have rights | Check IAM policies, use `sudo`, or fix file permissions (`chmod`) |
| `Connection refused` | Nothing is listening on that port | Is the service running? Check `docker ps` or `systemctl status` |
| `No such file or directory` | File path is wrong | Use absolute paths, check spelling, verify file exists |
| `Out of memory` | Not enough RAM | Use a bigger instance type, or reduce batch size |
| `Terraform lock` | Someone else is using the state | Run `terraform force-unlock <ID>` or wait |
| `Image pull backoff` | Kubernetes can't download image | Check ECR permissions, image tag, and credentials |

### The Debug Checklist

When everything seems broken:

1. [ ] Read the error message carefully (really!)
2. [ ] Check the logs (`docker logs`, CloudWatch, `journalctl`)
3. [ ] Verify environment variables (`env`, `echo $VAR`)
4. [ ] Check network connectivity (`ping`, `curl`, `telnet`)
5. [ ] Verify IAM permissions (`aws sts get-caller-identity`)
6. [ ] Check resource limits (CPU, memory, disk space)
7. [ ] Try the simplest version first (local before cloud)
8. [ ] Google the exact error message
9. [ ] Ask for help with the logs attached

---

## 🎓 What You Learned

| Concept | Before | After |
|---------|--------|-------|
| Model | "A magic AI file" | "A trained neural network that can be loaded and used for predictions" |
| Docker | "A blue whale logo" | "A tool that packages apps with all dependencies into portable containers" |
| AWS IAM | "Something about security" | "The system that controls who can access what resources" |
| AWS EC2 | "A virtual server thing" | "A rentable computer in the cloud that I can SSH into and run Docker" |
| Terraform | "Infrastructure as code?" | "A blueprint tool that creates and manages cloud resources reproducibly" |
| CI/CD | "Automated testing?" | "A robot that tests my code, builds my app, and deploys it automatically" |

---

## 🚀 What's Next?

Now that you understand the basics, you can:

1. **Customize the model** — Retrain with your own data using `train.py`
2. **Add monitoring** — Set up CloudWatch dashboards and alerts
3. **Enable HTTPS** — Add SSL certificates via cert-manager or ACM
4. **Add authentication** — Protect your API with API keys or JWT
5. **Scale globally** — Deploy to multiple regions with Route 53
6. **Optimize costs** — Use Spot Instances, Lambda, or SageMaker Serverless

---

> **Remember:** Every expert was once a beginner. The fact that you made it through this guide means you now understand more about cloud deployment than 90% of developers. Keep building!
