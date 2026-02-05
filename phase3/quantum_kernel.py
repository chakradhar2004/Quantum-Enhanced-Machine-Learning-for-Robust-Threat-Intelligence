"""
Phase 3 - Quantum kernel analysis for threat intelligence.
Implements quantum kernel methods for feature space analysis.
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import rbf_kernel
import matplotlib.pyplot as plt
import seaborn as sns
import os


class QuantumKernelAnalyzer:
    """Quantum-inspired kernel analysis for threat intelligence."""
    
    def __init__(self, gamma=1.0):
        """
        Initialize analyzer.
        
        Args:
            gamma (float): RBF kernel parameter
        """
        self.gamma = gamma
        self.K = None
        self.K_domain = None
        self.K_malware = None
    
    def compute_rbf_kernel(self, X, gamma=None):
        """
        Compute RBF kernel matrix (quantum-inspired).
        
        Args:
            X: Feature matrix
            gamma: Kernel parameter (uses self.gamma if None)
            
        Returns:
            Kernel matrix
        """
        if gamma is None:
            gamma = self.gamma
        
        K = rbf_kernel(X, gamma=gamma)
        return K
    
    def analyze_domain_kernel(self, df_domain, label_col='label'):
        """
        Analyze domain dataset kernel properties.
        
        Args:
            df_domain: Domain PCA dataframe
            label_col: Label column name
            
        Returns:
            dict: Kernel analysis results
        """
        X = df_domain.drop(columns=label_col).values
        y = df_domain[label_col].values
        
        # Compute kernel
        self.K_domain = self.compute_rbf_kernel(X)
        
        # Analyze by class
        benign_idx = np.where(y == 0)[0]
        malicious_idx = np.where(y == 1)[0]
        
        # Within-class similarity
        K_benign_benign = self.K_domain[np.ix_(benign_idx, benign_idx)]
        K_mal_mal = self.K_domain[np.ix_(malicious_idx, malicious_idx)]
        
        # Between-class similarity
        K_cross = self.K_domain[np.ix_(benign_idx, malicious_idx)]
        
        results = {
            'kernel_shape': self.K_domain.shape,
            'benign_similarity': K_benign_benign.mean(),
            'malicious_similarity': K_mal_mal.mean(),
            'cross_similarity': K_cross.mean(),
            'separability': (K_benign_benign.mean() + K_mal_mal.mean()) / 2 - K_cross.mean(),
        }
        
        return results
    
    def analyze_malware_kernel(self, df_malware, label_col='label'):
        """
        Analyze malware dataset kernel properties.
        
        Args:
            df_malware: Malware PCA dataframe
            label_col: Label column name
            
        Returns:
            dict: Kernel analysis results
        """
        X = df_malware.drop(columns=label_col).values
        y = df_malware[label_col].values
        
        # Compute kernel
        self.K_malware = self.compute_rbf_kernel(X)
        
        # Analyze by class
        benign_idx = np.where(y == 0)[0]
        malware_idx = np.where(y == 1)[0]
        
        # Within-class similarity
        K_benign_benign = self.K_malware[np.ix_(benign_idx, benign_idx)]
        K_mal_mal = self.K_malware[np.ix_(malware_idx, malware_idx)]
        
        # Between-class similarity
        K_cross = self.K_malware[np.ix_(benign_idx, malware_idx)]
        
        results = {
            'kernel_shape': self.K_malware.shape,
            'benign_similarity': K_benign_benign.mean(),
            'malware_similarity': K_mal_mal.mean(),
            'cross_similarity': K_cross.mean(),
            'separability': (K_benign_benign.mean() + K_mal_mal.mean()) / 2 - K_cross.mean(),
        }
        
        return results
    
    def get_kernel_eigenvectors(self, K, n_components=10):
        """
        Compute kernel eigenvectors for analysis.
        
        Args:
            K: Kernel matrix
            n_components: Number of eigenvectors to compute
            
        Returns:
            tuple: (eigenvalues, eigenvectors)
        """
        # Normalize kernel
        K_norm = K / K.max()
        
        # Compute eigendecomposition
        eigenvalues, eigenvectors = np.linalg.eigh(K_norm)
        
        # Sort by eigenvalues
        idx = np.argsort(-eigenvalues)
        eigenvalues = eigenvalues[idx][:n_components]
        eigenvectors = eigenvectors[:, idx][:, :n_components]
        
        return eigenvalues, eigenvectors
    
    def plot_kernel_heatmap(self, K, title, output_path=None):
        """
        Plot kernel heatmap.
        
        Args:
            K: Kernel matrix
            title: Plot title
            output_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Sample for visualization if too large
        if K.shape[0] > 500:
            K_viz = K[:500, :500]
        else:
            K_viz = K
        
        sns.heatmap(K_viz, cmap='viridis', ax=ax, cbar_kws={'label': 'Kernel Similarity'})
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"[SUCCESS] Saved kernel heatmap to {output_path}")
        
        plt.close()
    
    def plot_kernel_spectrum(self, K, title, output_path=None):
        """
        Plot kernel spectrum (eigenvalue distribution).
        
        Args:
            K: Kernel matrix
            title: Plot title
            output_path: Path to save figure
        """
        eigenvalues, _ = self.get_kernel_eigenvectors(K, n_components=min(100, K.shape[0]))
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(eigenvalues, 'o-', linewidth=2, markersize=6)
        ax.set_xlabel('Component Index', fontsize=12)
        ax.set_ylabel('Eigenvalue', fontsize=12)
        ax.set_title(f'{title} - Kernel Spectrum', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"[SUCCESS] Saved kernel spectrum to {output_path}")
        
        plt.close()


class QuantumKernelComparison:
    """Compare quantum kernels between domain and malware datasets."""
    
    def __init__(self, gamma=1.0, output_dir='../results'):
        """
        Initialize comparator.
        
        Args:
            gamma: Kernel parameter
            output_dir: Output directory
        """
        self.analyzer = QuantumKernelAnalyzer(gamma=gamma)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def analyze_and_compare(self, df_domain, df_malware):
        """
        Analyze both datasets and generate comparisons.
        
        Args:
            df_domain: Domain PCA dataframe
            df_malware: Malware PCA dataframe
            
        Returns:
            dict: Combined analysis results
        """
        print("[INFO] Analyzing domain dataset...")
        domain_results = self.analyzer.analyze_domain_kernel(df_domain)
        
        print("[INFO] Analyzing malware dataset...")
        malware_results = self.analyzer.analyze_malware_kernel(df_malware)
        
        # Generate heatmaps
        self.analyzer.plot_kernel_heatmap(
            self.analyzer.K_domain,
            'Domain Dataset: Quantum Kernel Matrix',
            os.path.join(self.output_dir, '08_domain_kernel_heatmap.png')
        )
        
        self.analyzer.plot_kernel_heatmap(
            self.analyzer.K_malware,
            'Malware Dataset: Quantum Kernel Matrix',
            os.path.join(self.output_dir, '09_malware_kernel_heatmap.png')
        )
        
        # Generate spectrum plots
        self.analyzer.plot_kernel_spectrum(
            self.analyzer.K_domain,
            'Domain Dataset',
            os.path.join(self.output_dir, '10_domain_kernel_spectrum.png')
        )
        
        self.analyzer.plot_kernel_spectrum(
            self.analyzer.K_malware,
            'Malware Dataset',
            os.path.join(self.output_dir, '11_malware_kernel_spectrum.png')
        )
        
        # Plot comparison
        self._plot_comparison(domain_results, malware_results)
        
        return {
            'domain': domain_results,
            'malware': malware_results
        }
    
    def _plot_comparison(self, domain_results, malware_results):
        """Plot side-by-side comparison of kernel properties."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Domain metrics
        metrics = ['benign_similarity', 'malicious_similarity', 'cross_similarity', 'separability']
        domain_vals = [domain_results[m] for m in metrics]
        
        axes[0].bar(range(len(metrics)), domain_vals, alpha=0.7, color='steelblue')
        axes[0].set_xticks(range(len(metrics)))
        axes[0].set_xticklabels(metrics, rotation=45, ha='right')
        axes[0].set_ylabel('Value', fontsize=12)
        axes[0].set_title('Domain Dataset: Kernel Properties', fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Malware metrics
        malware_vals = [malware_results[m] for m in metrics]
        
        axes[1].bar(range(len(metrics)), malware_vals, alpha=0.7, color='coral')
        axes[1].set_xticks(range(len(metrics)))
        axes[1].set_xticklabels(metrics, rotation=45, ha='right')
        axes[1].set_ylabel('Value', fontsize=12)
        axes[1].set_title('Malware Dataset: Kernel Properties', fontsize=14, fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '12_kernel_properties_comparison.png'),
                   dpi=300, bbox_inches='tight')
        print("[SUCCESS] Saved kernel properties comparison")
        plt.close()


if __name__ == "__main__":
    # Example usage
    import pickle
    
    # Load preprocessed data
    domain_path = './domain/domain_pca.csv'
    malware_path = './ember/ember_pca.csv'
    
    if os.path.exists(domain_path) and os.path.exists(malware_path):
        df_domain = pd.read_csv(domain_path)
        df_malware = pd.read_csv(malware_path)
        
        comparator = QuantumKernelComparison()
        results = comparator.analyze_and_compare(df_domain, df_malware)
        
        print("\n[INFO] Analysis complete!")
        print(f"Domain separability: {results['domain']['separability']:.4f}")
        print(f"Malware separability: {results['malware']['separability']:.4f}")
