"""
Phase 3 - Visualization utilities for threat intelligence analysis.
Provides functions for plotting PCA, distributions, and classification results.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import os


class Phase3Visualizer:
    """Visualization utilities for Phase 3 analysis."""
    
    def __init__(self, output_dir='../results', style='seaborn-v0_8-darkgrid'):
        """
        Initialize visualizer.
        
        Args:
            output_dir (str): Directory to save visualizations
            style (str): Matplotlib style
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        plt.style.use(style)
        sns.set_palette('husl')
    
    def plot_pca_variance(self, pca_domain, pca_malware, filename='01_pca_variance_explained.png'):
        """Plot PCA variance explained by components."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Domain
        axes[0].bar(range(1, 5), pca_domain.explained_variance_ratio_, alpha=0.7, color='steelblue')
        axes[0].plot(range(1, 5), np.cumsum(pca_domain.explained_variance_ratio_), 
                     'ro-', linewidth=2, markersize=8)
        axes[0].set_xlabel('Principal Component', fontsize=12)
        axes[0].set_ylabel('Variance Explained', fontsize=12)
        axes[0].set_title('Domain Dataset: PCA Variance Explained', fontsize=14, fontweight='bold')
        axes[0].set_xticks(range(1, 5))
        axes[0].grid(True, alpha=0.3)
        
        # Malware
        axes[1].bar(range(1, 5), pca_malware.explained_variance_ratio_, alpha=0.7, color='coral')
        axes[1].plot(range(1, 5), np.cumsum(pca_malware.explained_variance_ratio_), 
                     'ro-', linewidth=2, markersize=8)
        axes[1].set_xlabel('Principal Component', fontsize=12)
        axes[1].set_ylabel('Variance Explained', fontsize=12)
        axes[1].set_title('Malware Dataset: PCA Variance Explained', fontsize=14, fontweight='bold')
        axes[1].set_xticks(range(1, 5))
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"[SUCCESS] Saved {filename}")
        plt.close()
    
    def plot_pca_scatter(self, df_domain, df_malware, pca_domain, pca_malware, 
                        filename='02_pca_scatter_plots.png'):
        """Plot 2D PCA scatter plots."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Domain
        scatter1 = axes[0].scatter(df_domain['PC1'], df_domain['PC2'],
                                  c=df_domain['label'], cmap='RdYlGn_r',
                                  alpha=0.6, s=30, edgecolors='black', linewidth=0.5)
        axes[0].set_xlabel(f"PC1 ({pca_domain.explained_variance_ratio_[0]:.1%})", fontsize=12)
        axes[0].set_ylabel(f"PC2 ({pca_domain.explained_variance_ratio_[1]:.1%})", fontsize=12)
        axes[0].set_title('Domain Dataset: PCA Space (PC1 vs PC2)', fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        plt.colorbar(scatter1, ax=axes[0], label='Label (0=Benign, 1=Malicious)')
        
        # Malware
        scatter2 = axes[1].scatter(df_malware['PC1'], df_malware['PC2'],
                                  c=df_malware['label'], cmap='RdYlGn_r',
                                  alpha=0.6, s=30, edgecolors='black', linewidth=0.5)
        axes[1].set_xlabel(f"PC1 ({pca_malware.explained_variance_ratio_[0]:.1%})", fontsize=12)
        axes[1].set_ylabel(f"PC2 ({pca_malware.explained_variance_ratio_[1]:.1%})", fontsize=12)
        axes[1].set_title('Malware Dataset: PCA Space (PC1 vs PC2)', fontsize=14, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        plt.colorbar(scatter2, ax=axes[1], label='Label (0=Benign, 1=Malware)')
        
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"[SUCCESS] Saved {filename}")
        plt.close()
    
    def plot_pca_3d(self, df_domain, df_malware, filename='03_pca_3d_visualization.png'):
        """Plot 3D PCA visualization."""
        fig = plt.figure(figsize=(14, 5))
        
        # Domain 3D
        ax1 = fig.add_subplot(121, projection='3d')
        scatter1 = ax1.scatter(df_domain['PC1'], df_domain['PC2'], df_domain['PC3'],
                              c=df_domain['label'], cmap='RdYlGn_r', alpha=0.6, s=20)
        ax1.set_xlabel('PC1', fontsize=10)
        ax1.set_ylabel('PC2', fontsize=10)
        ax1.set_zlabel('PC3', fontsize=10)
        ax1.set_title('Domain Dataset: 3D PCA', fontsize=12, fontweight='bold')
        
        # Malware 3D
        ax2 = fig.add_subplot(122, projection='3d')
        scatter2 = ax2.scatter(df_malware['PC1'], df_malware['PC2'], df_malware['PC3'],
                              c=df_malware['label'], cmap='RdYlGn_r', alpha=0.6, s=20)
        ax2.set_xlabel('PC1', fontsize=10)
        ax2.set_ylabel('PC2', fontsize=10)
        ax2.set_zlabel('PC3', fontsize=10)
        ax2.set_title('Malware Dataset: 3D PCA', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"[SUCCESS] Saved {filename}")
        plt.close()
    
    def plot_pc_distributions(self, df_domain, df_malware, filename='04_pc_distributions.png'):
        """Plot principal component distributions."""
        fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        
        # Domain distributions
        for i in range(4):
            col = f'PC{i+1}'
            axes[0, i].hist(df_domain[df_domain['label']==0][col],
                           alpha=0.6, bins=30, label='Benign', color='green')
            axes[0, i].hist(df_domain[df_domain['label']==1][col],
                           alpha=0.6, bins=30, label='Malicious', color='red')
            axes[0, i].set_title(f'Domain: {col} Distribution', fontsize=11, fontweight='bold')
            axes[0, i].set_xlabel('Value')
            axes[0, i].set_ylabel('Frequency')
            axes[0, i].legend()
            axes[0, i].grid(True, alpha=0.3)
        
        # Malware distributions
        for i in range(4):
            col = f'PC{i+1}'
            axes[1, i].hist(df_malware[df_malware['label']==0][col],
                           alpha=0.6, bins=30, label='Benign', color='green')
            axes[1, i].hist(df_malware[df_malware['label']==1][col],
                           alpha=0.6, bins=30, label='Malware', color='red')
            axes[1, i].set_title(f'Malware: {col} Distribution', fontsize=11, fontweight='bold')
            axes[1, i].set_xlabel('Value')
            axes[1, i].set_ylabel('Frequency')
            axes[1, i].legend()
            axes[1, i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"[SUCCESS] Saved {filename}")
        plt.close()
    
    def plot_correlation_heatmaps(self, df_domain, df_malware, filename='05_correlation_heatmaps.png'):
        """Plot correlation heatmaps."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Domain correlation
        corr_domain = df_domain.corr()
        sns.heatmap(corr_domain, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   ax=axes[0], square=True, cbar_kws={'label': 'Correlation'})
        axes[0].set_title('Domain PCA: Correlation Matrix', fontsize=14, fontweight='bold')
        
        # Malware correlation
        corr_malware = df_malware.corr()
        sns.heatmap(corr_malware, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   ax=axes[1], square=True, cbar_kws={'label': 'Correlation'})
        axes[1].set_title('Malware PCA: Correlation Matrix', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"[SUCCESS] Saved {filename}")
        plt.close()
    
    def plot_class_separation(self, df_domain, df_malware, filename='06_class_separation_analysis.png'):
        """Plot class separation analysis."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Domain class means
        domain_benign = df_domain[df_domain['label']==0].drop('label', axis=1).mean()
        domain_malicious = df_domain[df_domain['label']==1].drop('label', axis=1).mean()
        
        x_pos = np.arange(4)
        width = 0.35
        axes[0].bar(x_pos - width/2, domain_benign, width, label='Benign', alpha=0.8)
        axes[0].bar(x_pos + width/2, domain_malicious, width, label='Malicious', alpha=0.8)
        axes[0].set_xlabel('Principal Component', fontsize=12)
        axes[0].set_ylabel('Mean Value', fontsize=12)
        axes[0].set_title('Domain: Class Mean Separation', fontsize=14, fontweight='bold')
        axes[0].set_xticks(x_pos)
        axes[0].set_xticklabels([f'PC{i+1}' for i in range(4)])
        axes[0].legend()
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Malware class means
        malware_benign = df_malware[df_malware['label']==0].drop('label', axis=1).mean()
        malware_malicious = df_malware[df_malware['label']==1].drop('label', axis=1).mean()
        
        axes[1].bar(x_pos - width/2, malware_benign, width, label='Benign', alpha=0.8)
        axes[1].bar(x_pos + width/2, malware_malicious, width, label='Malware', alpha=0.8)
        axes[1].set_xlabel('Principal Component', fontsize=12)
        axes[1].set_ylabel('Mean Value', fontsize=12)
        axes[1].set_title('Malware: Class Mean Separation', fontsize=14, fontweight='bold')
        axes[1].set_xticks(x_pos)
        axes[1].set_xticklabels([f'PC{i+1}' for i in range(4)])
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"[SUCCESS] Saved {filename}")
        plt.close()
    
    def plot_boxplots(self, df_domain, df_malware, filename='07_boxplot_analysis.png'):
        """Plot boxplot analysis."""
        fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        
        # Domain boxplots
        for i in range(4):
            col = f'PC{i+1}'
            data_to_plot = [df_domain[df_domain['label']==0][col],
                           df_domain[df_domain['label']==1][col]]
            axes[0, i].boxplot(data_to_plot, labels=['Benign', 'Malicious'])
            axes[0, i].set_ylabel('Value')
            axes[0, i].set_title(f'Domain: {col}', fontsize=11, fontweight='bold')
            axes[0, i].grid(True, alpha=0.3)
        
        # Malware boxplots
        for i in range(4):
            col = f'PC{i+1}'
            data_to_plot = [df_malware[df_malware['label']==0][col],
                           df_malware[df_malware['label']==1][col]]
            axes[1, i].boxplot(data_to_plot, labels=['Benign', 'Malware'])
            axes[1, i].set_ylabel('Value')
            axes[1, i].set_title(f'Malware: {col}', fontsize=11, fontweight='bold')
            axes[1, i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"[SUCCESS] Saved {filename}")
        plt.close()
    
    def plot_all(self, df_domain, df_malware, pca_domain, pca_malware):
        """Generate all visualizations."""
        print("\n[INFO] Generating all visualizations...")
        self.plot_pca_variance(pca_domain, pca_malware)
        self.plot_pca_scatter(df_domain, df_malware, pca_domain, pca_malware)
        self.plot_pca_3d(df_domain, df_malware)
        self.plot_pc_distributions(df_domain, df_malware)
        self.plot_correlation_heatmaps(df_domain, df_malware)
        self.plot_class_separation(df_domain, df_malware)
        self.plot_boxplots(df_domain, df_malware)
        print("[SUCCESS] All visualizations generated!")
