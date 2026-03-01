
# 2. GitHub Actions CI/CD Pipeline
cicd_content = """name: 🚀 CNN MLOps CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths-ignore:
      - '**.md'
      - 'docs/**'
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly retraining check

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: cnn-classifier
  EKS_CLUSTER: cnn-mlops-cluster
  MODEL_BUCKET: cnn-mlops-models
  PYTHON_VERSION: '3.9'

jobs:
  # ============================================================================
  # STAGE 1: Code Quality & Validation
  # ============================================================================
  code-quality:
    runs-on: ubuntu-latest
    name: 🔍 Code Quality Checks
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
          pip install black flake8 isort mypy bandit safety

      - name: Run Black (formatting check)
        run: black --check --diff src/ tests/

      - name: Run isort (import sorting)
        run: isort --check-only --diff src/ tests/

      - name: Run Flake8 (linting)
        run: flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203

      - name: Run MyPy (type checking)
        run: mypy src/ --ignore-missing-imports

      - name: Run Bandit (security check)
        run: bandit -r src/ -f json -o bandit-report.json || true

      - name: Run Safety (dependency check)
        run: safety check -r requirements.txt --json --output safety-report.json || true

      - name: Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json

  # ============================================================================
  # STAGE 2: Data Validation & Tests
  # ============================================================================
  data-validation:
    runs-on: ubuntu-latest
    name: 📊 Data Validation
    needs: code-quality
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install DVC
        run: |
          pip install dvc[s3] dvc-gdrive
          dvc --version

      - name: Pull DVC data
        run: |
          dvc remote modify myremote access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}
          dvc remote modify myremote secret_access_key ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          dvc pull

      - name: Validate data schema
        run: |
          python -m src.data.validate_schema \
            --data-path data/raw \
            --schema-path config/data_schema.yaml

      - name: Check data drift
        run: |
          python -m src.data.check_drift \
            --reference-data data/reference \
            --current-data data/raw \
            --output drift_report.json

      - name: Upload drift report
        uses: actions/upload-artifact@v4
        with:
          name: drift-report
          path: drift_report.json

  # ============================================================================
  # STAGE 3: Unit & Integration Tests
  # ============================================================================
  testing:
    runs-on: ubuntu-latest
    name: 🧪 Testing Suite
    needs: [code-quality, data-validation]
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: mlflow_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx

      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=src --cov-report=xml --cov-report=html

      - name: Run integration tests
        env:
          MLFLOW_TRACKING_URI: postgresql://test:test@localhost:5432/mlflow_test
        run: |
          pytest tests/integration -v --cov-append

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: |
            coverage.xml
            htmlcov/

      - name: Code Coverage Summary
        uses: irongut/CodeCoverageSummary@v1.3.0
        with:
          filename: coverage.xml
          badge: true
          fail_below_min: true
          format: markdown
          hide_branch_rate: false
          hide_complexity: true
          indicators: true
          output: both
          thresholds: '60 80'

  # ============================================================================
  # STAGE 4: Model Training (Conditional)
  # ============================================================================
  train-model:
    runs-on: ubuntu-latest
    name: 🧠 Model Training
    needs: testing
    if: github.ref == 'refs/heads/main' || contains(github.event.head_commit.message, '[train]')
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install dvc[s3]

      - name: Pull data
        run: dvc pull

      - name: Start MLflow Server
        run: |
          pip install mlflow psycopg2-binary
          mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns &
          sleep 5

      - name: Train model
        env:
          MLFLOW_TRACKING_URI: http://localhost:5000
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          python -m src.training.train \
            --config config/training.yaml \
            --experiment-name "cnn-classifier-${{ github.sha }}" \
            --epochs 50 \
            --batch-size 32

      - name: Evaluate model
        run: |
          python -m src.training.evaluate \
            --model-path models/latest.pt \
            --test-data data/test \
            --output metrics.json

      - name: Check performance threshold
        run: |
          python -c "
          import json
          with open('metrics.json') as f:
              metrics = json.load(f)
          acc = metrics['accuracy']
          print(f'Model Accuracy: {acc:.4f}')
          if acc < 0.85:
              raise ValueError(f'Accuracy {acc:.4f} below threshold 0.85')
          "

      - name: Upload model artifacts
        uses: actions/upload-artifact@v4
        with:
          name: model-artifacts
          path: |
            models/
            metrics.json

      - name: Push model to S3
        run: |
          aws s3 sync models/ s3://${{ env.MODEL_BUCKET }}/models/${{ github.sha }}/
          echo "Model uploaded to s3://${{ env.MODEL_BUCKET }}/models/${{ github.sha }}/"

  # ============================================================================
  # STAGE 5: Build & Push Docker Images
  # ============================================================================
  build-images:
    runs-on: ubuntu-latest
    name: 🐳 Build & Push Images
    needs: [testing, train-model]
    if: always() && (needs.train-model.result == 'success' || needs.train-model.result == 'skipped')
    strategy:
      matrix:
        service: [api, streamlit, training]
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-${{ github.sha }}
          restore-keys: |
            ${{ runner.os }}-buildx-

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.${{ matrix.service }}
          push: true
          tags: |
            ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}-${{ matrix.service }}:${{ github.sha }}
            ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}-${{ matrix.service }}:latest
          cache-from: type=local,src=/tmp/.buildx-cache
          cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
          build-args: |
            MODEL_VERSION=${{ github.sha }}
            BUILD_DATE=${{ github.event.head_commit.timestamp }}

      - name: Move cache
        run: |
          rm -rf /tmp/.buildx-cache
          mv /tmp/.buildx-cache-new /tmp/.buildx-cache

      - name: Scan image for vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}-${{ matrix.service }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: actions/upload-artifact@v4
        with:
          name: trivy-${{ matrix.service }}
          path: trivy-results.sarif

  # ============================================================================
  # STAGE 6: Deploy to Development
  # ============================================================================
  deploy-dev:
    runs-on: ubuntu-latest
    name: 🚀 Deploy to Dev
    needs: build-images
    if: github.ref == 'refs/heads/develop'
    environment:
      name: development
      url: http://dev.cnn-mlops.example.com
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Install kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: 'v1.28.0'

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER }}

      - name: Update Kustomize images
        run: |
          cd k8s/overlays/dev
          kustomize edit set image \
            api=${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}-api:${{ github.sha }} \
            streamlit=${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}-streamlit:${{ github.sha }}

      - name: Deploy to EKS
        run: |
          kustomize build k8s/overlays/dev | kubectl apply -f -
          kubectl rollout status deployment/api -n cnn-mlops-dev --timeout=300s
          kubectl rollout status deployment/streamlit -n cnn-mlops-dev --timeout=300s

      - name: Run smoke tests
        run: |
          kubectl port-forward svc/api 8080:80 -n cnn-mlops-dev &
          sleep 5
          curl -f http://localhost:8080/health || exit 1
          curl -f http://localhost:8080/metrics || exit 1

  # ============================================================================
  # STAGE 7: Deploy to Production (Manual Approval)
  # ============================================================================
  deploy-prod:
    runs-on: ubuntu-latest
    name: 🚀 Deploy to Production
    needs: build-images
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: http://cnn-mlops.example.com
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Install kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: 'v1.28.0'

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER }}

      - name: Update Kustomize images
        run: |
          cd k8s/overlays/prod
          kustomize edit set image \
            api=${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}-api:${{ github.sha }} \
            streamlit=${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}-streamlit:${{ github.sha }}

      - name: Deploy to EKS (Canary)
        run: |
          # Deploy canary (20% traffic)
          kustomize build k8s/overlays/prod | kubectl apply -f -
          kubectl rollout status deployment/api-canary -n cnn-mlops-prod --timeout=300s

      - name: Run production smoke tests
        run: |
          kubectl port-forward svc/api-canary 8080:80 -n cnn-mlops-prod &
          sleep 5
          curl -f http://localhost:8080/health
          
          # Run load test
          docker run --network=host loadimpact/k6 run --vus 10 --duration 30s \
            -e API_URL=http://localhost:8080 tests/k6/load_test.js

      - name: Promote to full deployment
        if: success()
        run: |
          kubectl patch service api -n cnn-mlops-prod -p '{"spec":{"selector":{"version":"${{ github.sha }}"}}}'
          kubectl rollout status deployment/api -n cnn-mlops-prod --timeout=300s

      - name: Rollback on failure
        if: failure()
        run: |
          echo "Deployment failed, rolling back..."
          kubectl rollout undo deployment/api -n cnn-mlops-prod

  # ============================================================================
  # STAGE 8: Notification
  # ============================================================================
  notify:
    runs-on: ubuntu-latest
    name: 📢 Notify Team
    needs: [deploy-dev, deploy-prod]
    if: always()
    steps:
      - name: Send Slack notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#mlops-alerts'
          text: |
            🚀 CNN MLOps Pipeline Completed
            Branch: ${{ github.ref }}
            Commit: ${{ github.sha }}
            Author: ${{ github.actor }}
            Status: ${{ job.status }}
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
"""

with open(f"{project_root}/.github/workflows/ci-cd.yml", "w") as f:
    f.write(cicd_content)

print("✅ GitHub Actions CI/CD pipeline created")
