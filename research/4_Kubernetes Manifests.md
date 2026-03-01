
# 4. Kubernetes Manifests

# Base deployment
k8s_base_deployment = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: cnn-api
  labels:
    app: cnn-api
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: cnn-api
  template:
    metadata:
      labels:
        app: cnn-api
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: cnn-mlops-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: api
        image: cnn-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: MODEL_PATH
          value: "/app/models"
        - name: MLFLOW_TRACKING_URI
          valueFrom:
            configMapKeyRef:
              name: cnn-config
              key: mlflow.uri
        - name: AWS_REGION
          valueFrom:
            configMapKeyRef:
              name: cnn-config
              key: aws.region
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: model-storage
          mountPath: /app/models
          readOnly: true
      volumes:
      - name: tmp
        emptyDir: {}
      - name: model-storage
        persistentVolumeClaim:
          claimName: model-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: cnn-api
  labels:
    app: cnn-api
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: cnn-api
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cnn-mlops-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/cnn-mlops-role
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: cnn-config
data:
  mlflow.uri: "http://mlflow-service:5000"
  aws.region: "us-east-1"
  model.name: "cnn-classifier"
"""

# Horizontal Pod Autoscaler
k8s_hpa = """apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cnn-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cnn-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
"""

# Ingress
k8s_ingress = """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cnn-api-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/CERT_ID
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
  - host: api.cnn-mlops.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cnn-api
            port:
              number: 80
"""

# Kustomization base
kustomization_base = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - hpa.yaml
  - ingress.yaml

commonLabels:
  project: cnn-mlops
  managed-by: kustomize

images:
  - name: cnn-api
    newName: ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cnn-classifier-api
    newTag: latest
"""

# Development overlay
kustomization_dev = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: cnn-mlops-dev

resources:
  - ../../base

namePrefix: dev-

commonLabels:
  environment: development

replicas:
  - name: cnn-api
    count: 2

patchesStrategicMerge:
  - |
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: cnn-api
    spec:
      template:
        spec:
          containers:
          - name: api
            resources:
              requests:
                memory: "256Mi"
                cpu: "100m"
              limits:
                memory: "512Mi"
                cpu: "500m"
"""

# Production overlay with canary
kustomization_prod = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: cnn-mlops-prod

resources:
  - ../../base
  - canary.yaml

namePrefix: prod-

commonLabels:
  environment: production

replicas:
  - name: cnn-api
    count: 5

patchesStrategicMerge:
  - |
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: cnn-api
    spec:
      template:
        spec:
          containers:
          - name: api
            resources:
              requests:
                memory: "1Gi"
                cpu: "500m"
              limits:
                memory: "4Gi"
                cpu: "2000m"
            env:
            - name: LOG_LEVEL
              value: "WARNING"
"""

# Canary deployment for production
canary_yaml = """apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: cnn-api
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cnn-api
  service:
    port: 80
    targetPort: 8000
  analysis:
    interval: 30s
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m
    webhooks:
    - name: load-test
      url: http://flagger-loadtester.test/
      timeout: 5s
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 http://cnn-api-canary/"
"""

# Write files
with open(f"{project_root}/k8s/base/deployment.yaml", "w") as f:
    f.write(k8s_base_deployment)

with open(f"{project_root}/k8s/base/hpa.yaml", "w") as f:
    f.write(k8s_hpa)

with open(f"{project_root}/k8s/base/ingress.yaml", "w") as f:
    f.write(k8s_ingress)

with open(f"{project_root}/k8s/base/kustomization.yaml", "w") as f:
    f.write(kustomization_base)

with open(f"{project_root}/k8s/overlays/dev/kustomization.yaml", "w") as f:
    f.write(kustomization_dev)

with open(f"{project_root}/k8s/overlays/prod/kustomization.yaml", "w") as f:
    f.write(kustomization_prod)

with open(f"{project_root}/k8s/overlays/prod/canary.yaml", "w") as f:
    f.write(canary_yaml)

print("✅ Kubernetes manifests created (Base + Dev/Prod overlays)")
