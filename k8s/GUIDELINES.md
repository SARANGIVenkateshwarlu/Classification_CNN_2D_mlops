# Kubernetes Deployment Guidelines

## Solar Panel Classifier — K8s Enterprise Deployment

This document provides step-by-step instructions for deploying the Solar Panel Classifier on Kubernetes at enterprise scale.

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Step-by-Step Deployment](#-step-by-step-deployment)
- [Environment Overlays](#-environment-overlays)
- [Verification & Testing](#-verification--testing)
- [Scaling & Operations](#-scaling--operations)
- [Troubleshooting](#-troubleshooting)
- [Security Hardening](#-security-hardening)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         INGRESS (NGINX)                          │
│              TLS 1.3 | Rate Limiting | WAF Rules                 │
│                                                                  │
│   api.yourdomain.com  ──────▶  FastAPI Service (Port 80)        │
│   app.yourdomain.com  ──────▶  Streamlit Service (Port 80)      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                      SERVICE (ClusterIP)                         │
│           Internal Load Balancing | Session Affinity             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐   ┌──────────▼──────────┐   ┌─────▼──────┐
│  API Pod 1   │   │     API Pod 2       │   │  API Pod N │
│  (Port 8000) │   │     (Port 8000)     │   │(Port 8000) │
│ ┌──────────┐ │   │    ┌──────────┐     │   │ ┌────────┐ │
│ │ TF Model │ │   │    │ TF Model │     │   │ │TF Model│ │
│ └──────────┘ │   │    └──────────┘     │   │ └────────┘ │
└──────────────┘   └─────────────────────┘   └────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    SHARED RESOURCES                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ ConfigMap  │  │    PVC     │  │ ServiceAcc │                │
│  │   (env)    │  │ (models)   │  │   (IRSA)   │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│              HORIZONTAL POD AUTOSCALER (HPA)                     │
│              CPU: 70% | Memory: 80% | 3–20 Pods                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Matrix

| Resource | File | Purpose |
|----------|------|---------|
| Namespace | `namespace.yaml` | Logical isolation |
| ConfigMap | `configmap.yaml` | Non-secret configuration |
| Deployment | `deployment.yaml` | API pod specification |
| Service | `service.yaml` | Internal networking |
| Ingress | `ingress.yaml` | External HTTPS routing |
| HPA | `hpa.yaml` | Auto-scaling rules |
| PVC | `pvc.yaml` | Shared model storage |
| ServiceAccount | `serviceaccount.yaml` | IAM/IRSA integration |
| NetworkPolicy | `networkpolicy.yaml` | Zero-trust networking |

---

## 📋 Prerequisites

### Required Tools

```bash
# Install kubectl (v1.28+)
curl -LO "https://dl.k8s/release/$(curl -L -s https://dl.k8s/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Kustomize (v5.0+)
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/

# Verify
kubectl version --client
kustomize version
```

### Required Cluster Add-ons

| Add-on | Purpose | Installation |
|--------|---------|--------------|
| **NGINX Ingress Controller** | External routing | [Install Guide](https://kubernetes.github.io/ingress-nginx/deploy/) |
| **cert-manager** | TLS certificates | [Install Guide](https://cert-manager.io/docs/installation/) |
| **metrics-server** | HPA metrics | `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml` |
| **EBS CSI Driver** | Persistent volumes | [Install Guide](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html) |

### EKS-Specific Prerequisites (if using AWS EKS)

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Configure AWS IAM Authenticator
# Ensure your kubeconfig points to the correct cluster
aws eks update-kubeconfig --region us-east-1 --name solar-panel-cluster
```

---

## ⚡ Quick Start

```bash
# 1. Clone repository
cd Classification_CNN_2D

# 2. Deploy base manifests (development defaults)
kubectl apply -k k8s/base

# 3. Verify deployment
kubectl get all -n solar-panel-classifier

# 4. Access locally (port-forward)
kubectl port-forward svc/solar-panel-api-service 8000:80 -n solar-panel-classifier
# Open http://localhost:8000/docs
```

---

## 📖 Step-by-Step Deployment

### Step 1: Prepare the Namespace

```bash
# Create the namespace first
kubectl apply -f k8s/base/namespace.yaml

# Verify
kubectl get namespace solar-panel-classifier
```

### Step 2: Configure Environment Variables

Edit `k8s/base/configmap.yaml` to match your environment:

```yaml
data:
  API_PORT: "8000"
  API_HOST: "0.0.0.0"
  MODEL_PRELOAD: "true"
  LOG_LEVEL: "INFO"
  MODEL_PATH: "/app/models/trained_effnet_finetune.keras"
```

Apply:
```bash
kubectl apply -f k8s/base/configmap.yaml
```

### Step 3: Set Up Model Storage (PVC)

The PersistentVolumeClaim expects a StorageClass named `ebs-sc`.

**For AWS EKS with EBS CSI:**
```bash
# Create the storage class first
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
parameters:
  type: gp3
  encrypted: "true"
EOF

kubectl apply -f k8s/base/pvc.yaml
```

**For local/minikube:**
```bash
# Use standard storage class
kubectl patch pvc model-pvc -n solar-panel-classifier --type='json' \
  -p='[{"op": "replace", "path": "/spec/storageClassName", "value":"standard"}]'
```

### Step 4: Upload Model to PVC

Create a temporary pod to copy models:

```bash
# Create a temporary upload pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: model-uploader
  namespace: solar-panel-classifier
spec:
  containers:
  - name: uploader
    image: busybox
    command: ["sleep", "3600"]
    volumeMounts:
    - name: model-volume
      mountPath: /models
  volumes:
  - name: model-volume
    persistentVolumeClaim:
      claimName: model-pvc
EOF

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/model-uploader -n solar-panel-classifier --timeout=60s

# Copy models from local
kubectl cp models/trained_effnet_finetune.keras \
  solar-panel-classifier/model-uploader:/models/

# Verify
kubectl exec -it model-uploader -n solar-panel-classifier -- ls -la /models

# Clean up
kubectl delete pod model-uploader -n solar-panel-classifier
```

### Step 5: Configure ServiceAccount & RBAC (EKS IRSA)

For AWS EKS with IAM Roles for Service Accounts:

```bash
# 1. Create IAM OIDC provider for your cluster
eksctl utils associate-iam-oidc-provider \
  --cluster solar-panel-cluster \
  --approve

# 2. Create IAM policy for S3/ECR access
cat <<EOF > solar-panel-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::solar-panel-classifier-models-*",
        "arn:aws:s3:::solar-panel-classifier-models-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name SolarPanelClassifierPolicy \
  --policy-document file://solar-panel-policy.json

# 3. Create IAM role and associate with service account
eksctl create iamserviceaccount \
  --name solar-panel-sa \
  --namespace solar-panel-classifier \
  --cluster solar-panel-cluster \
  --attach-policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/SolarPanelClassifierPolicy \
  --approve

# 4. Update the service account annotation in k8s/base/serviceaccount.yaml
#    with the generated role ARN
```

Apply RBAC:
```bash
kubectl apply -f k8s/base/serviceaccount.yaml
kubectl apply -f k8s/base/networkpolicy.yaml
```

### Step 6: Deploy the Application

```bash
# Apply the deployment
kubectl apply -f k8s/base/deployment.yaml

# Apply the service
kubectl apply -f k8s/base/service.yaml

# Verify pods are running
kubectl get pods -n solar-panel-classifier -w
```

Expected output:
```
NAME                                READY   STATUS    RESTARTS   AGE
solar-panel-api-7d9f4b8c5-x2abc   1/1     Running   0          45s
solar-panel-api-7d9f4b8c5-y3def   1/1     Running   0          45s
solar-panel-api-7d9f4b8c5-z4ghi   1/1     Running   0          45s
```

### Step 7: Configure Ingress

Update `k8s/base/ingress.yaml` with your domain:

```yaml
spec:
  tls:
    - hosts:
        - api.yourdomain.com    # ← Replace
        - app.yourdomain.com    # ← Replace
      secretName: solar-panel-tls
  rules:
    - host: api.yourdomain.com  # ← Replace
    - host: app.yourdomain.com  # ← Replace
```

Create the TLS certificate:
```bash
# Using cert-manager (recommended)
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

kubectl apply -f k8s/base/ingress.yaml
```

### Step 8: Enable Auto-Scaling (HPA)

```bash
# Ensure metrics-server is running
kubectl get pods -n kube-system | grep metrics-server

# Apply HPA
kubectl apply -f k8s/base/hpa.yaml

# Verify
kubectl get hpa -n solar-panel-classifier
```

Expected output:
```
NAME                  REFERENCE                    TARGETS   MINPODS   MAXPODS   REPLICAS
solar-panel-api-hpa   Deployment/solar-panel-api   5%/70%    3         20        3
```

---

## 🌍 Environment Overlays

### Development Overlay

```bash
# Deploy with development settings (1 replica, debug logging)
kubectl apply -k k8s/overlays/dev

# Features:
# - 1 replica minimum
# - LOG_LEVEL=DEBUG
# - Smaller resource requests
# - dev-latest image tag
```

### Production Overlay

```bash
# Deploy with production settings (5 replicas, high resources)
kubectl apply -k k8s/overlays/prod

# Features:
# - 5 replicas minimum
# - Higher CPU/memory limits
# - LOG_LEVEL=INFO
# - Version-pinned image tag
```

### Custom Overlay

Create your own overlay:

```bash
mkdir -p k8s/overlays/staging
cat <<EOF > k8s/overlays/staging/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: solar-panel-classifier-staging
namePrefix: staging-
resources:
  - ../../base
replicas:
  - name: solar-panel-api
    count: 2
configMapGenerator:
  - name: solar-panel-config
    behavior: merge
    literals:
      - LOG_LEVEL=DEBUG
images:
  - name: solar-panel-classifier
    newTag: staging-$(git rev-parse --short HEAD)
EOF

kubectl apply -k k8s/overlays/staging
```

---

## ✅ Verification & Testing

### Check All Resources

```bash
# Namespace resources
kubectl get all -n solar-panel-classifier

# Detailed pod status
kubectl describe pods -n solar-panel-classifier

# Deployment status
kubectl get deployment solar-panel-api -n solar-panel-classifier

# Service endpoints
kubectl get endpoints -n solar-panel-classifier

# Ingress status
kubectl get ingress -n solar-panel-classifier

# HPA status
kubectl get hpa -n solar-panel-classifier
```

### Test API Endpoints

```bash
# Port-forward for local testing
kubectl port-forward svc/solar-panel-api-service 8000:80 -n solar-panel-classifier

# Test health endpoint
curl http://localhost:8000/health

# Test model info
curl http://localhost:8000/model/info

# Test prediction (with image)
curl -X POST "http://localhost:8000/api/v1/predict?top_k=3" \
  -F "file=@Data/Clean/Clean\ \(1\).jpeg"
```

### View Logs

```bash
# All pods logs
kubectl logs -l app=solar-panel-api -n solar-panel-classifier --tail=100

# Specific pod
kubectl logs solar-panel-api-7d9f4b8c5-x2abc -n solar-panel-classifier -f

# Previous container logs (if crashed)
kubectl logs solar-panel-api-7d9f4b8c5-x2abc -n solar-panel-classifier --previous
```

---

## 📈 Scaling & Operations

### Manual Scaling

```bash
# Scale to 10 replicas
kubectl scale deployment solar-panel-api --replicas=10 -n solar-panel-classifier

# Scale back to 3
kubectl scale deployment solar-panel-api --replicas=3 -n solar-panel-classifier
```

### Rolling Updates

```bash
# Update image
kubectl set image deployment/solar-panel-api \
  api=solar-panel-classifier:v1.1.0 \
  -n solar-panel-classifier

# Watch rollout status
kubectl rollout status deployment/solar-panel-api -n solar-panel-classifier

# Rollback if needed
kubectl rollout undo deployment/solar-panel-api -n solar-panel-classifier
```

### Resource Monitoring

```bash
# Pod metrics
kubectl top pods -n solar-panel-classifier

# Node metrics
kubectl top nodes

# Describe HPA events
kubectl describe hpa solar-panel-api-hpa -n solar-panel-classifier
```

---

## 🐛 Troubleshooting

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| Pod stuck `Pending` | `kubectl describe pod <name> -n solar-panel-classifier` | Check PVC binding, node resources, taints |
| Pod `CrashLoopBackOff` | `kubectl logs <pod> -n solar-panel-classifier` | Check model file exists, env vars correct |
| HPA not scaling | `kubectl describe hpa -n solar-panel-classifier` | Ensure metrics-server is installed |
| Ingress not working | `kubectl describe ingress -n solar-panel-classifier` | Check NGINX controller, DNS records |
| Image pull error | `kubectl describe pod <name>` | Verify ECR login, image tag exists |
| Permission denied | `kubectl auth can-i --list` | Check ServiceAccount RBAC bindings |

### Common Commands

```bash
# Get events sorted by time
kubectl get events -n solar-panel-classifier --sort-by='.lastTimestamp'

# Debug with ephemeral container
kubectl debug -it solar-panel-api-xxx -n solar-panel-classifier --image=busybox --target=api

# Check network connectivity between pods
kubectl exec -it solar-panel-api-xxx -n solar-panel-classifier -- wget -qO- http://localhost:8000/health
```

---

## 🔒 Security Hardening

### Network Policies

The `networkpolicy.yaml` restricts traffic:
- **Ingress:** Only from NGINX ingress controller and same-namespace pods
- **Egress:** Only DNS (port 53) and HTTP/HTTPS (ports 80/443)

Verify enforcement:
```bash
kubectl get networkpolicies -n solar-panel-classifier
```

### Pod Security

The deployment enforces:
- `runAsNonRoot: true`
- `runAsUser: 1000`
- `allowPrivilegeEscalation: false`
- `capabilities: drop: [ALL]`

### Secrets Management

For sensitive data (API keys, database passwords):

```bash
# Create secret
kubectl create secret generic solar-panel-secrets \
  --from-literal=DB_PASSWORD=xxx \
  --from-literal=API_KEY=yyy \
  -n solar-panel-classifier

# Mount in deployment (add to containers.volumeMounts)
# - name: secrets-volume
#   mountPath: /app/secrets
#   readOnly: true
```

---

## 📚 Reference

- [Kustomize Documentation](https://kubectl.docs.kubernetes.io/guides/introduction/kustomize/)
- [Kubernetes Ingress NGINX](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [AWS EKS Best Practices](https://docs.aws.amazon.com/eks/latest/userguide/best-practices.html)
