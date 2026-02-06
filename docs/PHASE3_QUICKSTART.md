# Phase 3: Quick Start Guide

## What's New?

Complete Phase 3 implementation for quantum-enhanced threat intelligence with:
- ✅ Jupyter notebook (`notebooks/05_phase3_analysis.ipynb`)
- ✅ Python preprocessing module (`phase3/preprocessing.py`)
- ✅ Visualization utilities (`phase3/visualization.py`)
- ✅ Quantum kernel analysis (`phase3/quantum_kernel.py`)
- ✅ Main execution script (`phase3/phase3_main.py`)
- ✅ 12 publication-quality visualizations
- ✅ Comprehensive documentation

## 🚀 Quick Start

### Option 1: Jupyter Notebook (Recommended for Exploration)
```bash
cd notebooks
jupyter notebook 05_phase3_analysis.ipynb
```

### Option 2: Command Line (For Batch Processing)
```bash
cd phase3
python phase3_main.py --all
```

### Option 3: Python API (For Integration)
```python
from phase3 import Phase3Preprocessor, Phase3Visualizer

# Load and preprocess
df = pd.read_csv('data/domains/processed/domain_features.csv')
X = df.drop('label', axis=1)
y = df['label']

preprocessor = Phase3Preprocessor(n_components=4)
X_transformed = preprocessor.fit_transform(X, y)

# Visualize
visualizer = Phase3Visualizer()
visualizer.plot_pca_variance(pca1, pca2)
```

## 📊 What Gets Generated?

### Data Files
- `phase3/domain/domain_pca.csv` - Domain features reduced to 4 PCA components
- `phase3/ember/ember_pca.csv` - Malware features reduced to 4 PCA components
- `phase3/domain/*.pkl` - Saved preprocessing models
- `phase3/ember/*.pkl` - Saved preprocessing models

### Visualizations (in `results/`)
1. PCA variance explained analysis
2. 2D scatter plots (PC1 vs PC2)
3. 3D PCA projections
4. Principal component distributions
5. Correlation heatmaps
6. Class separation analysis
7. Boxplot analysis
8. Quantum kernel heatmaps
9. Kernel spectrum plots
10. Kernel properties comparison

### Reports
- `results/phase3_summary.json` - Statistical summary
- `results/kernel_analysis.json` - Quantum kernel metrics

## 📚 Documentation

- [Phase 3 README](phase3/README.md) - Detailed module documentation
- [Implementation Summary](PHASE3_IMPLEMENTATION.md) - What was implemented
- [Notebook](notebooks/05_phase3_analysis.ipynb) - Interactive analysis walkthrough

## 🔧 Module Overview

### preprocessing.py
```python
from phase3 import Phase3Preprocessor

# Simple API
preprocessor = Phase3Preprocessor(n_components=4)
X_reduced = preprocessor.fit_transform(X, y)

# With multiple transforms
X_train_reduced = preprocessor.fit_transform(X_train, y_train)
X_test_reduced = preprocessor.transform(X_test)

# Save/load models
preprocessor.save('path/to/save')
loaded = Phase3Preprocessor.load('path/to/load')
```

### visualization.py
```python
from phase3 import Phase3Visualizer

# Generate all visualizations
visualizer = Phase3Visualizer(output_dir='results')
visualizer.plot_all(df_domain, df_malware, pca_domain, pca_malware)

# Or individual plots
visualizer.plot_pca_variance(pca_domain, pca_malware)
visualizer.plot_pca_scatter(df_domain, df_malware, pca_domain, pca_malware)
visualizer.plot_correlation_heatmaps(df_domain, df_malware)
```

### quantum_kernel.py
```python
from phase3 import QuantumKernelComparison

# Quantum kernel analysis
comparator = QuantumKernelComparison(gamma=1.0, output_dir='results')
results = comparator.analyze_and_compare(df_domain, df_malware)

# Results contain separability metrics:
# - benign_similarity
# - malicious_similarity  
# - cross_similarity
# - separability score
```

### phase3_main.py
```bash
# All analysis
python phase3_main.py --all

# Specific components
python phase3_main.py --domain --visualize
python phase3_main.py --kernel --malware
python phase3_main.py --visualize --output-dir custom_results

# Custom configurations
python phase3_main.py --all --n-components 8 --output-dir results
```

## 📈 Key Metrics Computed

### PCA Analysis
- Variance explained per component
- Cumulative variance
- Total variance retained with 4 components
- Component loadings

### Kernel Analysis
- Within-class similarity (benign/benign, malicious/malicious)
- Between-class similarity (benign/malicious)
- Separability score
- Kernel spectrum (eigenvalues)
- Kernel rank

### Statistical Analysis
- Class distribution
- Mean values per component
- Standard deviations
- Correlation matrices
- Quartile statistics

## 🎯 Next Steps

1. **Run the notebook** to explore the data interactively
2. **Generate visualizations** to understand class separation
3. **Analyze quantum kernels** to assess feature space quality
4. **Use reduced features** for downstream ML models (Phase 4)

## ⚠️ Notes

- Requires: pandas, numpy, scikit-learn, matplotlib, seaborn
- Input data expected in: `data/domains/processed/` and `data/malware/processed/`
- Outputs saved to: `phase3/` (processed data) and `results/` (visualizations)
- If dataset missing, synthetic data is generated for demonstration

## 🆘 Troubleshooting

### Import Error?
```python
import sys
sys.path.insert(0, '../phase3')
from phase3 import Phase3Preprocessor
```

### Missing Data?
The notebook creates synthetic data if real data is missing

### CUDA/GPU Issues?
Preprocessing uses CPU - no GPU acceleration needed

## 📞 Support

See [Phase 3 README](phase3/README.md) for detailed documentation.
