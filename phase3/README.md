# Phase 3: Quantum-Enhanced Threat Intelligence Analysis

## Overview

Phase 3 implements dimensionality reduction, quantum kernel analysis, and comprehensive visualization for the quantum-enhanced threat intelligence system.

## Directory Structure

```
phase3/
├── __init__.py                    # Package initialization
├── preprocessing.py               # PCA preprocessing utilities
├── visualization.py              # Visualization utilities
├── quantum_kernel.py             # Quantum kernel analysis
├── phase3_main.py               # Main execution script
├── domain/                       # Domain dataset processing
│   ├── domain_pca.csv           # Processed domain features (4 PCA components)
│   ├── domain_pca_model.pkl     # Trained PCA model
│   └── domain_scaler.pkl        # Fitted StandardScaler
├── ember/                        # Malware dataset processing
│   ├── ember_pca.csv            # Processed malware features (4 PCA components)
│   ├── ember_pca_model.pkl      # Trained PCA model
│   └── ember_scaler.pkl         # Fitted StandardScaler
└── README.md                     # This file
```

## Features

### 1. Dimensionality Reduction
- **PCA (Principal Component Analysis)**: Reduces high-dimensional features to 4 principal components
- **StandardScaler**: Normalizes features before PCA
- Preserves maximum variance in lower dimensions

### 2. Quantum Kernel Analysis
- **RBF Kernel**: Computes quantum-inspired kernel similarities
- **Class Separability**: Measures separation between benign and malicious samples
- **Kernel Spectrum**: Analyzes eigenvalue distribution
- **Kernel Heatmaps**: Visualizes sample similarities

### 3. Comprehensive Visualizations
1. **PCA Variance Analysis** - Explained variance per component
2. **2D PCA Scatter Plots** - Class distribution in PCA space
3. **3D PCA Visualization** - Multi-dimensional feature space
4. **Distribution Analysis** - PC distributions by class
5. **Correlation Heatmaps** - Feature correlations
6. **Class Separation** - Mean values comparison
7. **Boxplot Analysis** - Statistical distributions
8. **Kernel Heatmaps** - Similarity matrices
9. **Kernel Spectrum** - Eigenvalue distributions
10. **Kernel Properties** - Separability metrics

## Usage

### Method 1: Jupyter Notebook
Open and run the notebook at `notebooks/05_phase3_analysis.ipynb`

```jupyter
jupyter notebook notebooks/05_phase3_analysis.ipynb
```

### Method 2: Command Line

Run the main script with various options:

```bash
# Run all analysis
python phase3/phase3_main.py --all

# Run specific analyses
python phase3/phase3_main.py --domain --visualize
python phase3/phase3_main.py --kernel
python phase3/phase3_main.py --malware --kernel

# Custom output directory
python phase3/phase3_main.py --all --output-dir /path/to/output
```

### Method 3: Python API

```python
from phase3 import Phase3Preprocessor, Phase3Visualizer, QuantumKernelComparison

# Preprocess datasets
preprocessor = Phase3Preprocessor(n_components=4)
X_transformed = preprocessor.fit_transform(X, y)

# Visualize results
visualizer = Phase3Visualizer(output_dir='results')
visualizer.plot_all(df_domain, df_malware, pca_domain, pca_malware)

# Quantum kernel analysis
comparator = QuantumKernelComparison()
results = comparator.analyze_and_compare(df_domain, df_malware)
```

## Input Data

### Domain Dataset
- **Source**: `data/domains/processed/domain_features.csv`
- **Columns**: Feature columns + 'label'
- **Label**: 0 = Benign, 1 = Malicious Domain

### Malware Dataset
- **Source**: `data/malware/processed/ember_features.csv`
- **Columns**: Feature columns + 'label'
- **Label**: 0 = Benign, 1 = Malware

## Output Files

### Processed Data
- `phase3/domain/domain_pca.csv` - Domain features reduced to 4 PCA components
- `phase3/ember/ember_pca.csv` - Malware features reduced to 4 PCA components

### Models
- `phase3/domain/domain_scaler.pkl` - StandardScaler for domain data
- `phase3/domain/domain_pca_model.pkl` - Fitted PCA model for domain
- `phase3/ember/ember_scaler.pkl` - StandardScaler for malware data
- `phase3/ember/ember_pca_model.pkl` - Fitted PCA model for malware

### Visualizations
All visualizations saved to `results/`:
1. `01_pca_variance_explained.png`
2. `02_pca_scatter_plots.png`
3. `03_pca_3d_visualization.png`
4. `04_pc_distributions.png`
5. `05_correlation_heatmaps.png`
6. `06_class_separation_analysis.png`
7. `07_boxplot_analysis.png`
8. `08_domain_kernel_heatmap.png`
9. `09_malware_kernel_heatmap.png`
10. `10_domain_kernel_spectrum.png`
11. `11_malware_kernel_spectrum.png`
12. `12_kernel_properties_comparison.png`

### Reports
- `results/phase3_summary.json` - Statistical summary
- `results/kernel_analysis.json` - Quantum kernel metrics

## Key Metrics

### PCA Analysis
- **Explained Variance Ratio**: Percentage of variance explained per component
- **Cumulative Variance**: Total variance retained with 4 components
- **Total Variance Explained**: Sum of all component contributions

### Kernel Analysis
- **Benign/Malicious Similarity**: Within-class kernel similarity
- **Cross Similarity**: Between-class kernel similarity
- **Separability Score**: Measure of class separation in kernel space

## Performance Considerations

- **Dataset Size**: Handles datasets with thousands of samples efficiently
- **Dimensionality**: Reduces features from 100+ to 4 dimensions
- **Computation Time**: O(n × d²) for PCA, O(n²) for kernel matrices
- **Memory**: Kernel matrices can be large for big datasets (sampled for visualization)

## Citation

If you use Phase 3 in your research, please cite:

```bibtex
@software{phase3_2024,
  title={Phase 3: Quantum-Enhanced Threat Intelligence},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/Quantum-Enhanced_Threat_Intelligence}
}
```

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions, please create an issue or pull request on GitHub.
