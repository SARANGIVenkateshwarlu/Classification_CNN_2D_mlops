### 🎓 Research-Grade CNN Image Classification Template

📋 Complete Workflow Architecture

┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: DATA ENGINEERING                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Raw Data → Validation → Cleaning → Augmentation → Splitting → Versioning   │
│     │           │          │           │            │            │          │
│     ▼           ▼          ▼           ▼            ▼            ▼          │
│   Images    Integrity   Duplicate   Albumentations  Stratified    DVC      │
│             Check       Removal     Pipeline        Split         Git      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2: EXPLORATORY DATA ANALYSIS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Class Distribution Analysis (handle imbalance)                           │
│  • Image Quality Assessment (resolution, corruption)                        │
│  • Sample Visualization (grid plots)                                        │
│  • Dimensionality Analysis (PCA on flattened images)                        │
│  • Statistical Summary (mean, std per channel)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: MODEL ARCHITECTURE SELECTION                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  10+ CNN Architectures (Chronological & Performance-based)                  │
│                                                                             │
│  Classical (2012-2015)          Modern (2016-2019)         SOTA (2020+)    │
│  ├─ LeNet-5 (Baseline)          ├─ ResNet-18/34/50        ├─ EfficientNet │
│  ├─ AlexNet (Deep Learning)     ├─ ResNet-101/152         │   (B0-B7)     │
│  ├─ VGG-16/19 (Depth)           ├─ DenseNet-121/169       ├─ Vision       │
│  └─ Network In Network          ├─ Inception-v3           │   Transformer │
│                                 ├─ Xception               ├─ ConvNeXt      │
│                                 └─ MobileNetV2            └─ CoAtNet       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: TRAINING STRATEGY (Research-Grade)               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Optimization:           Regularization:           Augmentation:            │
│  • AdamW (default)       • Dropout (0.2-0.5)       • RandomResizedCrop      │
│  • SGD + Momentum        • Label Smoothing         • Horizontal Flip        │
│  • RMSprop               • Stochastic Depth        • Color Jitter           │
│  • Lion (2023)           • Mixup/CutMix            • RandAugment            │
│                          • Weight Decay            • AutoAugment            │
│                                                                             │
│  Learning Rate Scheduling:                                                  │
│  • Cosine Annealing (default)                                               │
│  • One Cycle Policy (fast.ai)                                               │
│  • Warm Restart (SGDR)                                                      │
│  • ReduceLROnPlateau                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 5: EVALUATION & COMPARISON                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Metrics:                    Analysis:                                      │
│  • Accuracy (Top-1, Top-5)   • Confusion Matrix                             │
│  • Precision/Recall/F1       • ROC-AUC Curves                               │
│  • Matthews Correlation      • Per-Class Performance                        │
│  • Cohen's Kappa             • Error Analysis                               │
│  • Inference Time            • Statistical Significance (t-test)            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 6: HYPERPARAMETER OPTIMIZATION                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Method: Bayesian Optimization (Optuna) or Population Based Training        │
│                                                                             │
│  Search Space:                                                              │
│  • Learning Rate: [1e-5, 1e-1] (log scale)                                  │
│  • Batch Size: [16, 32, 64, 128]                                            │
│  • Dropout Rate: [0.1, 0.5]                                                 │
│  • Augmentation Strength: [0.0, 1.0]                                        │
│  • Label Smoothing: [0.0, 0.2]                                              │
│  • Optimizer: [AdamW, SGD, Lion]                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 7: FINAL MODEL & DEPLOYMENT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Ensemble Methods (Weighted Averaging, Stacking)                          │
│  • Knowledge Distillation (teacher-student)                                 │
│  • Quantization (INT8) for edge deployment                                  │
│  • Export: SavedModel (.pb), ONNX, TFLite, H5                               │
│  • Documentation: Model Card (Google's framework)                           │
└─────────────────────────────────────────────────────────────────────────────┘

---

🔬 Detailed Phase Descriptions
PHASE 1: Data Engineering (Research Standards)
1.1 Data Validation Protocol
Purpose: Ensure data quality before any model training
Steps:

    Integrity Check: Verify all images are readable (no corruption)
    Format Standardization: Convert all to RGB, consistent format (JPEG/PNG)
    Duplicate Detection: Use perceptual hashing (pHash) to find near-duplicates
    Outlier Detection: Identify images that don't match class distribution

Research Reference:

    "A Large-scale Study of Image Classification" (Google Research, 2021)
    "Data Validation for Machine Learning" (MLSys, 2019)

1.2 Data Augmentation Strategy (Albumentations Library)
Geometric Transformations:
plain
Copy

• RandomResizedCrop: Scale (0.8, 1.0), Ratio (0.75, 1.33)
• HorizontalFlip: p=0.5
• VerticalFlip: p=0.3 (if applicable)
• Rotation: ±15 degrees
• Affine: Translation (±10%), Shear (±10°)

Photometric Transformations:
plain
Copy

• ColorJitter: Brightness (0.2), Contrast (0.2), Saturation (0.2), Hue (0.1)
• RandomBrightnessContrast: p=0.5
• GaussianBlur: Limit (3x3), p=0.3
• GaussNoise: var_limit=(10.0, 50.0), p=0.3
• Normalize: ImageNet statistics (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

Advanced Augmentations:
plain
Copy

• Cutout/GridMask: Random erasing of regions
• Mixup: α=0.4 (blends two images)
• CutMix: α=1.0 (cuts and mixes patches)
• RandAugment: N=2, M=9 (AutoML augmentation)

Research Reference:

    "RandAugment: Practical Automated Data Augmentation" (CVPR, 2020)
    "CutMix: Regularization Strategy to Train Strong Classifiers" (ICCV, 2019)

1.3 Data Splitting Strategy
Stratified K-Fold Cross-Validation (k=5):

    Ensures each fold has same class distribution
    Reduces variance in performance estimates
    Use for small datasets (<10k images)

Hold-out Validation (for large datasets):

    Train: 70%, Validation: 15%, Test: 15%
    Stratified split to maintain class balance
    Fixed random seed for reproducibility

PHASE 2: Exploratory Data Analysis (EDA)
2.1 Class Distribution Analysis

    Imbalance Ratio: Calculate max_class/min_class
    Handling Strategies:
        Class weights in loss function (inverse frequency)
        Oversampling: SMOTE, ADASYN (for tabular), or duplication
        Undersampling: Random or Tomek links

2.2 Image Statistics

    Resolution Analysis: Distribution of image sizes
    Aspect Ratio: Check for extreme ratios (may need padding)
    Channel Statistics: Mean, Std per channel (for normalization)

2.3 t-SNE/UMAP Visualization

    Project high-dimensional image features to 2D
    Visualize class separability
    Identify potential labeling errors

PHASE 3: Model Architecture Selection (10+ Models)
Tier 1: Baseline & Classical (Establish Baseline)
1. LeNet-5 (1998) - Yann LeCun

    Purpose: Historical baseline, very fast training
    Architecture: 2 Conv + 3 FC, ~60k parameters
    When to use: Tiny datasets (<1k images), embedded systems
    Input: 32×32 grayscale

2. AlexNet (2012) - Krizhevsky et al. (ImageNet Winner)

    Purpose: Proved deep learning works for vision
    Architecture: 5 Conv + 3 FC, 60M parameters, ReLU, Dropout
    When to use: Medium datasets, educational purposes
    Key Innovation: ReLU activation, GPU training, Dropout regularization

3. VGG-16/19 (2014) - Simonyan & Zisserman

    Purpose: Showed depth matters (16-19 layers)
    Architecture: 3×3 conv filters only, very uniform, 138M params
    When to use: Feature extraction, transfer learning base
    Key Innovation: Small filters (3×3) instead of large (11×11)

4. Network In Network (NiN) (2013)

    Purpose: MLPconv layers, global average pooling
    Architecture: Micro neural networks within conv layers
    When to use: Reducing parameters, preventing overfitting

Tier 2: Modern Architectures (ResNet Era)
5. ResNet-18/34/50/101/152 (2015) - He et al. (ImageNet Winner)

    Purpose: Solved vanishing gradient problem, very deep networks (152+ layers)
    Architecture: Residual connections (skip connections), BatchNorm
    When to use: Default choice for most tasks, excellent transfer learning
    Key Innovation: Residual learning: F(x) = H(x) - x
    Variants:
        ResNet-18/34: Basic blocks (2 layers)
        ResNet-50/101/152: Bottleneck blocks (3 layers, 1×1, 3×3, 1×1 conv)

6. DenseNet-121/169/201 (2017) - Huang et al.

    Purpose: Feature reuse, parameter efficiency
    Architecture: Dense connections (each layer connects to all others), 8M params
    When to use: Small datasets, memory-constrained environments
    Key Innovation: Feature concatenation instead of addition

7. Inception-v3 (2015) - Szegedy et al. (Google)

    Purpose: Multi-scale feature extraction
    Architecture: Inception modules (parallel convs of different sizes), 24M params
    When to use: When object sizes vary significantly
    Key Innovation: Factorized convolutions (7×7 → 7×1 + 1×7)

8. Xception (2017) - Chollet (Google)

    Purpose: Extreme version of Inception
    Architecture: Depthwise separable convolutions, 23M params
    When to use: Mobile/edge deployment, efficient inference
    Key Innovation: Channel-wise spatial convolutions

9. MobileNetV2 (2018) - Sandler et al. (Google)

    Purpose: Mobile and embedded vision
    Architecture: Inverted residuals, linear bottlenecks, 3.5M params
    When to use: Real-time mobile applications
    Key Innovation: Separable convolutions, width multiplier for scaling

Tier 3: State-of-the-Art (2020+)
10. EfficientNet-B0 to B7 (2019) - Tan & Le (Google)

    Purpose: Optimal scaling (depth, width, resolution jointly)
    Architecture: Compound scaling, MobileNetV2 blocks + SE blocks
    When to use: Production systems, best accuracy-efficiency tradeoff
    Key Innovation: Compound coefficient scaling (φ)
    Variants: B0 (5.3M params) to B7 (66M params)

11. Vision Transformer (ViT) (2020) - Dosovitskiy et al. (Google)

    Purpose: Apply Transformer architecture to images
    Architecture: Patch embedding + Transformer encoder, 86M params (ViT-Base)
    When to use: Large datasets (>10M images), when you have compute
    Key Innovation: Self-attention across image patches
    Note: Requires large pretraining (JFT-300M) or fine-tuning

12. ConvNeXt (2022) - Facebook AI

    Purpose: Modernize CNNs to match Transformers
    Architecture: Pure CNN with modern training techniques
    When to use: When you want Transformer performance with CNN simplicity
---
PHASE 4: Training Strategy (Research-Grade)
4.1 Optimization Configuration
Optimizer Selection:

| Optimizer          | Learning Rate | Weight Decay | Best For                          |
| ------------------ | ------------- | ------------ | --------------------------------- |
| **AdamW**          | 1e-3          | 0.01         | Default, most stable              |
| **SGD + Momentum** | 1e-2          | 5e-4         | Final convergence, generalization |
| **Lion** (2023)    | 3e-4          | 0.1          | Memory efficient, new SOTA        |
| **RAdam**          | 1e-3          | 0.01         | Warmup built-in                   |


---

Learning Rate Scheduling:
plain
Copy

1. Warmup: Linear increase for first 5 epochs (0 → base_lr)
2. Main Training: Cosine Annealing (base_lr → min_lr)
3. Cooldown: Final 10 epochs at min_lr

Loss Functions:

    CrossEntropyLoss (default)
    LabelSmoothingCrossEntropy (ε=0.1, prevents overconfidence)
    Focal Loss (for imbalanced datasets, γ=2.0)
    Bi-Tempered Loss (robust to noise)
---
4.2 Regularization Techniques
Dropout Strategy:

    Input layer: 0.2
    Hidden layers: 0.5
    Final layer: 0.3 (before classifier)

Advanced Regularization:

    Stochastic Depth (DropPath): Randomly drop layers during training (p=0.2)
    DropBlock: Structured dropout for conv layers
    Spectral Normalization: On discriminator (for GANs) or stabilizes training
---
4.3 Training Loop Best Practices
Mixed Precision Training:

    Use Automatic Mixed Precision (AMP) with bfloat16/float16
    2-3x faster training, half memory usage
    Loss scaling to prevent gradient underflow

Gradient Accumulation:

    Simulate large batch sizes with limited memory
    Effective batch size = batch_size × accumulation_steps

Exponential Moving Average (EMA):

    Maintain shadow weights: θ_ema = 0.999 × θ_ema + 0.001 × θ
    Use EMA weights for evaluation (more stable)
---

PHASE 5: Evaluation & Model Comparison
5.1 Primary Metrics
Classification Metrics:

    Top-1 Accuracy: % of correct predictions
    Top-5 Accuracy: Correct class in top 5 predictions
    Macro-F1: Average F1 across classes (handles imbalance)
    Cohen's Kappa: Agreement measure (accounts for chance)
    Matthews Correlation Coefficient (MCC): Balanced measure for binary/multiclass
---
Efficiency Metrics:

    Inference Time: ms per image (CPU & GPU)
    FLOPs: Floating point operations
    Parameters: Model size (MB)
    Memory Usage: Peak GPU/CPU memory
---

5.2 Statistical Comparison
Paired t-test: Compare two models' performance across folds
McNemar's Test: Compare models on specific examples
Effect Size: Cohen's d (practical significance, not just statistical)
5.3 Error Analysis
Confusion Matrix Analysis:

    Identify most confused class pairs
    Analyze false positives vs false negatives
---
Failure Modes:

    Adversarial examples
    Out-of-distribution samples
    Edge cases (occlusion, lighting)
---
PHASE 6: Hyperparameter Optimization
6.1 Search Strategy
Bayesian Optimization (Optuna):

    Builds probabilistic model of objective function
    Efficiently searches high-dimensional space
    Handles conditional parameters (e.g., Adam vs SGD hyperparams)
---

Population Based Training (PBT):

    Evolutionary approach, trains multiple models simultaneously
    Exploits and explores during training
    Good for large compute budgets

| Hyperparameter        | Range                          | Type        |
| --------------------- | ------------------------------ | ----------- |
| Learning Rate         | \[1e-5, 1e-1]                  | Log uniform |
| Batch Size            | \[16, 32, 64, 128]             | Choice      |
| Dropout               | \[0.1, 0.5]                    | Uniform     |
| Augmentation Strength | \[0.0, 1.0]                    | Uniform     |
| Label Smoothing       | \[0.0, 0.2]                    | Uniform     |
| Optimizer             | \[AdamW, SGD, Lion]            | Choice      |
| Weight Decay          | \[1e-5, 1e-2]                  | Log uniform |
| Scheduler             | \[cosine, one\_cycle, plateau] | Choice      |

---
6.3 Early Stopping for HPO

    Pruning: Stop unpromising trials early (median stopping rule)
    Max Trials: 100-200 depending on compute budget
    Timeout: 24-48 hours maximum
---

PHASE 7: Final Model & Deployment
7.1 Ensemble Methods
Weighted Average Ensemble:

    Train 5 models with different seeds
    Weights proportional to validation accuracy
    Soft voting (average probabilities)
---

Stacking (Super Learner):

    Train meta-learner (usually logistic regression) on base model predictions
    Use out-of-fold predictions to avoid leakage
---

7.2 Knowledge Distillation
Teacher-Student Training:

    Large teacher model (e.g., EfficientNet-B7) provides soft targets
    Small student model (e.g., MobileNet) learns from soft labels
    Temperature scaling (T=4) for softer probability distribution

---

7.3 Model Export Formats

| Format               | Extension   | Use Case                     |
| -------------------- | ----------- | ---------------------------- |
| **Keras/TensorFlow** | .h5, .keras | Research, Python deployment  |
| **SavedModel**       | directory   | TensorFlow Serving, TFX      |
| **ONNX**             | .onnx       | Cross-platform, optimization |
| **TensorFlow Lite**  | .tflite     | Mobile, edge devices         |
| **TorchScript**      | .pt         | PyTorch production           |
| **Quantized INT8**   | various     | 4x smaller, faster inference |

---

7.4 Model Documentation (Model Card)
Following Google's Model Cards framework:

    Model Details: Architecture, version, date
    Intended Use: Primary use cases, out-of-scope uses
    Factors: Relevant factors (demographics, environmental)
    Metrics: Performance across different subgroups
    Evaluation Data: Dataset details, preprocessing
    Training Data: Source, size, characteristics
    Quantitative Analyses: Performance metrics
    Ethical Considerations: Potential biases, fairness
    Caveats: Known limitations, recommendations

---

📊 Expected Results Template
Model Comparison Table


| Model           | Params | FLOPs | Top-1 Acc | Val Acc | Test Acc | Inference (ms) | GPU Mem (GB) |
| --------------- | ------ | ----- | --------- | ------- | -------- | -------------- | ------------ |
| LeNet-5         | 60K    | 0.4M  | -         | 65.2%   | 64.8%    | 2              | 0.5          |
| AlexNet         | 60M    | 714M  | 57.2%     | 78.5%   | 77.9%    | 8              | 1.2          |
| VGG-16          | 138M   | 15.5G | 71.5%     | 85.3%   | 84.7%    | 25             | 2.8          |
| ResNet-18       | 11M    | 1.8G  | 69.6%     | 87.2%   | 86.8%    | 12             | 1.0          |
| ResNet-50       | 25M    | 4.1G  | 76.0%     | 91.5%   | 91.1%    | 18             | 1.5          |
| DenseNet-121    | 8M     | 2.9G  | 74.9%     | 90.8%   | 90.3%    | 22             | 1.8          |
| Inception-v3    | 24M    | 5.7G  | 77.2%     | 91.2%   | 90.9%    | 28             | 2.1          |
| MobileNetV2     | 3.5M   | 300M  | 72.0%     | 88.5%   | 88.1%    | 15             | 0.8          |
| EfficientNet-B0 | 5.3M   | 390M  | 77.1%     | 92.3%   | 91.9%    | 20             | 1.1          |
| EfficientNet-B3 | 12M    | 1.8G  | 81.6%     | 94.1%   | 93.8%    | 35             | 1.9          |
| ViT-Base        | 86M    | 17.6G | 84.2%     | 94.8%   | 94.5%    | 45             | 3.2          |

Note: Numbers are illustrative and depend on your specific dataset

---

🔬 Research Paper References

    LeNet: LeCun et al., "Gradient-Based Learning Applied to Document Recognition" (1998)
    AlexNet: Krizhevsky et al., "ImageNet Classification with Deep CNNs" (NIPS 2012)
    VGG: Simonyan & Zisserman, "Very Deep Convolutional Networks" (ICLR 2015)
    ResNet: He et al., "Deep Residual Learning for Image Recognition" (CVPR 2016)
    DenseNet: Huang et al., "Densely Connected Convolutional Networks" (CVPR 2017)
    Inception: Szegedy et al., "Rethinking the Inception Architecture" (CVPR 2016)
    Xception: Chollet, "Xception: Deep Learning with Depthwise Separable Convolutions" (CVPR 2017)
    MobileNetV2: Sandler et al., "MobileNetV2: Inverted Residuals" (CVPR 2018)
    EfficientNet: Tan & Le, "EfficientNet: Rethinking Model Scaling" (ICML 2019)
    ViT: Dosovitskiy et al., "An Image is Worth 16x16 Words" (ICLR 2021)
    ConvNeXt: Liu et al., "A ConvNet for the 2020s" (CVPR 2022)
    Training Tips: He et al., "Bag of Tricks for Image Classification" (CVPR 2019)

---

✅ Execution Checklist

    [ ] Data Preparation: Validated, cleaned, augmented, split
    [ ] EDA: Distribution analysis, visualization, statistics
    [ ] Baseline: LeNet or simple CNN for reference
    [ ] Classical Models: AlexNet, VGG (if dataset >10k)
    [ ] Modern Models: ResNet-18/50, DenseNet (default choice)
    [ ] Efficient Models: MobileNet, EfficientNet (production)
    [ ] SOTA Models: ViT (if dataset >100k or transfer learning)
    [ ] Training: Proper augmentation, scheduling, regularization
    [ ] Evaluation: Multiple metrics, statistical tests
    [ ] HPO: Bayesian optimization for top-3 models
    [ ] Ensemble: Weighted average of best models
    [ ] Export: Multiple formats for deployment
    [ ] Documentation: Model card, README, requirements

This template follows the complete ML research lifecycle and ensures reproducible, publication-quality results for CNN image classification tasks.