
# 15. Create __init__.py files for all Python packages
import os

packages = [
    "src",
    "src/models",
    "src/data",
    "src/training",
    "src/inference",
    "src/api",
    "src/utils",
    "src/monitoring",
    "streamlit_app"
]

for pkg in packages:
    init_file = f"{project_root}/{pkg}/__init__.py"
    os.makedirs(os.path.dirname(init_file), exist_ok=True)
    with open(init_file, "w") as f:
        f.write(f'"""{pkg.replace("/", ".")} package."""\n')

print("✅ Python package __init__.py files created")

# 16. Create additional important files

# .gitignore
gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# ML & Data
*.pt
*.pth
*.ckpt
*.h5
*.hdf5
*.pkl
*.pickle
models/
!models/.gitkeep
data/
!data/.gitkeep
mlruns/
mlflow.db
wandb/

# DVC
.dvc
.dvcignore

# Environment
.env
.env.local
.env.*.local

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/
.nox/

# Terraform
.terraform/
.terraform.lock.hcl
*.tfstate
*.tfstate.*
*.tfvars

# Kubernetes
*.kubeconfig

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Temporary
tmp/
temp/
*.tmp
"""

with open(f"{project_root}/.gitignore", "w") as f:
    f.write(gitignore)

# .dockerignore
dockerignore = """# Git
.git
.gitignore

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/

# Testing
.pytest_cache/
.coverage
htmlcov/
tests/

# Documentation
docs/
*.md

# Data & Models (large files)
data/
models/*.pt
models/*.pth
*.h5

# Jupyter
notebooks/
.ipynb_checkpoints/

# MLflow
mlruns/
mlflow.db

# Terraform
terraform/
*.tfstate

# Local environment
.env
.env.local

# Temporary files
*.log
*.tmp
tmp/
temp/
"""

with open(f"{project_root}/.dockerignore", "w") as f:
    f.write(dockerignore)

# DVC .dvcignore
dvcignore = """# Add patterns of files dvc should ignore
.DS_Store
.gitignore
.git/
*.tmp
*.log
"""

with open(f"{project_root}/.dvcignore", "w") as f:
    f.write(dvcignore)

# pyproject.toml for modern Python packaging
pyproject_toml = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "cnn-mlops"
version = "1.0.0"
description = "Production-grade CNN Image Classification MLOps Platform"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "MLOps Team", email = "mlops@example.com"}
]
keywords = ["machine-learning", "deep-learning", "mlops", "cnn", "classification"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "fastapi>=0.103.0",
    "uvicorn[standard]>=0.23.0",
    "mlflow>=2.7.0",
    "prometheus-client>=0.17.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.5.0",
]

[project.urls]
Homepage = "https://github.com/your-org/cnn-mlops"
Documentation = "https://cnn-mlops.readthedocs.io"
Repository = "https://github.com/your-org/cnn-mlops.git"
Issues = "https://github.com/your-org/cnn-mlops/issues"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\b(eggs|\\.eggs|\\.git|\\.hg|\\.mypy_cache|\\.nox|\\.tox|\\.venv|_build|buck-out|build|dist|\\.dvc|mlruns)\\b
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "gpu: marks tests as requiring GPU",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/test_*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
"""

with open(f"{project_root}/pyproject.toml", "w") as f:
    f.write(pyproject_toml)

# Pre-commit config
precommit_config = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.9
        args: ['--line-length=100']

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile=black', '--line-length=100']

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ['--ignore-missing-imports']

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'src/', '-f', 'json', '-o', 'bandit-report.json']
        pass_filenames: false
"""

with open(f"{project_root}/.pre-commit-config.yaml", "w") as f:
    f.write(precommit_config)

# LICENSE
license_text = """MIT License

Copyright (c) 2024 CNN MLOps Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

with open(f"{project_root}/LICENSE", "w") as f:
    f.write(license_text)

# Create placeholder directories
placeholders = [
    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
    "models/.gitkeep",
    "logs/.gitkeep",
    "checkpoints/.gitkeep",
    "mlruns/.gitkeep"
]

for placeholder in placeholders:
    path = f"{project_root}/{placeholder}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("")

print("✅ Additional project files created (gitignore, dockerignore, pyproject.toml, etc.)")
