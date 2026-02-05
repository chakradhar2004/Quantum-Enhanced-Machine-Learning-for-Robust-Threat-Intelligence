"""
Phase 3: Quantum-Enhanced Threat Intelligence Analysis

This module provides tools for:
- PCA-based dimensionality reduction of domain and malware datasets
- Quantum kernel analysis and comparison
- Comprehensive data visualization
- Statistical analysis and reporting
"""

from .preprocessing import Phase3Preprocessor, preprocess_domain_dataset, preprocess_malware_dataset
from .visualization import Phase3Visualizer
from .quantum_kernel import QuantumKernelAnalyzer, QuantumKernelComparison

__version__ = '1.0.0'
__all__ = [
    'Phase3Preprocessor',
    'preprocess_domain_dataset',
    'preprocess_malware_dataset',
    'Phase3Visualizer',
    'QuantumKernelAnalyzer',
    'QuantumKernelComparison'
]
