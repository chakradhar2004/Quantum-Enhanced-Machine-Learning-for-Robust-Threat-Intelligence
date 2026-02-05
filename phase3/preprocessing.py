"""
Phase 3 - Preprocessing utilities for domain and malware datasets.
Handles PCA dimensionality reduction and feature standardization.
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pickle
import os
from pathlib import Path


class Phase3Preprocessor:
    """Unified preprocessor for Phase 3 domain and malware datasets."""
    
    def __init__(self, n_components=4):
        """
        Initialize the preprocessor.
        
        Args:
            n_components (int): Number of PCA components (default: 4)
        """
        self.n_components = n_components
        self.scaler = None
        self.pca = None
        self.feature_names = None
        
    def fit(self, X, y=None):
        """
        Fit the scaler and PCA on the data.
        
        Args:
            X: Feature matrix
            y: Labels (optional)
            
        Returns:
            self
        """
        # Standardize features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Apply PCA
        self.pca = PCA(n_components=self.n_components)
        self.pca.fit(X_scaled)
        
        return self
    
    def transform(self, X):
        """
        Transform data using fitted scaler and PCA.
        
        Args:
            X: Feature matrix
            
        Returns:
            Transformed feature matrix
        """
        if self.scaler is None or self.pca is None:
            raise ValueError("Preprocessor must be fitted before transform")
        
        X_scaled = self.scaler.transform(X)
        X_transformed = self.pca.transform(X_scaled)
        
        return X_transformed
    
    def fit_transform(self, X, y=None):
        """Fit and transform in one step."""
        self.fit(X, y)
        return self.transform(X)
    
    def get_variance_info(self):
        """Get PCA variance information."""
        return {
            'explained_variance_ratio': self.pca.explained_variance_ratio_,
            'total_variance_explained': sum(self.pca.explained_variance_ratio_),
            'cumulative_variance': np.cumsum(self.pca.explained_variance_ratio_)
        }
    
    def save(self, output_path):
        """Save preprocessor (scaler and PCA) to disk."""
        os.makedirs(output_path, exist_ok=True)
        
        with open(os.path.join(output_path, 'scaler.pkl'), 'wb') as f:
            pickle.dump(self.scaler, f)
        
        with open(os.path.join(output_path, 'pca.pkl'), 'wb') as f:
            pickle.dump(self.pca, f)
    
    @classmethod
    def load(cls, output_path):
        """Load preprocessor from disk."""
        with open(os.path.join(output_path, 'scaler.pkl'), 'rb') as f:
            scaler = pickle.load(f)
        
        with open(os.path.join(output_path, 'pca.pkl'), 'rb') as f:
            pca = pickle.load(f)
        
        instance = cls(n_components=pca.n_components_)
        instance.scaler = scaler
        instance.pca = pca
        
        return instance


def preprocess_domain_dataset(input_path, output_dir, n_components=4):
    """
    Preprocess domain dataset with PCA.
    
    Args:
        input_path (str): Path to domain features CSV
        output_dir (str): Directory to save processed data
        n_components (int): Number of PCA components
        
    Returns:
        tuple: (preprocessed_df, preprocessor, variance_info)
    """
    print("[INFO] Loading domain features...")
    df = pd.read_csv(input_path)
    
    print(f"[INFO] Original shape: {df.shape}")
    
    # Separate features and labels
    X = df.drop(columns='label').values
    y = df['label'].values
    
    # Create and fit preprocessor
    preprocessor = Phase3Preprocessor(n_components=n_components)
    X_transformed = preprocessor.fit_transform(X, y)
    
    # Create output dataframe
    df_processed = pd.DataFrame(
        X_transformed,
        columns=[f'PC{i+1}' for i in range(n_components)]
    )
    df_processed['label'] = y
    
    # Save processed data
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'domain_pca.csv')
    df_processed.to_csv(output_path, index=False)
    
    # Save preprocessor
    preprocessor.save(output_dir)
    
    variance_info = preprocessor.get_variance_info()
    
    print(f"[INFO] Processed shape: {df_processed.shape}")
    print(f"[INFO] Total variance explained: {variance_info['total_variance_explained']:.4f}")
    print(f"[SUCCESS] Saved to {output_path}")
    
    return df_processed, preprocessor, variance_info


def preprocess_malware_dataset(input_path, output_dir, n_components=4):
    """
    Preprocess malware dataset with PCA.
    
    Args:
        input_path (str): Path to malware features CSV
        output_dir (str): Directory to save processed data
        n_components (int): Number of PCA components
        
    Returns:
        tuple: (preprocessed_df, preprocessor, variance_info)
    """
    print("[INFO] Loading malware features...")
    df = pd.read_csv(input_path)
    
    print(f"[INFO] Original shape: {df.shape}")
    
    # Separate features and labels
    X = df.drop(columns='label').values
    y = df['label'].values
    
    # Create and fit preprocessor
    preprocessor = Phase3Preprocessor(n_components=n_components)
    X_transformed = preprocessor.fit_transform(X, y)
    
    # Create output dataframe
    df_processed = pd.DataFrame(
        X_transformed,
        columns=[f'PC{i+1}' for i in range(n_components)]
    )
    df_processed['label'] = y
    
    # Save processed data
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'ember_pca.csv')
    df_processed.to_csv(output_path, index=False)
    
    # Save preprocessor
    preprocessor.save(output_dir)
    
    variance_info = preprocessor.get_variance_info()
    
    print(f"[INFO] Processed shape: {df_processed.shape}")
    print(f"[INFO] Total variance explained: {variance_info['total_variance_explained']:.4f}")
    print(f"[SUCCESS] Saved to {output_path}")
    
    return df_processed, preprocessor, variance_info


if __name__ == "__main__":
    # Example usage
    domain_input = "../data/domains/processed/domain_features.csv"
    domain_output = "./ domain"
    
    if os.path.exists(domain_input):
        preprocess_domain_dataset(domain_input, domain_output)
    
    malware_input = "../data/malware/processed/ember_features.csv"
    malware_output = "./ember"
    
    if os.path.exists(malware_input):
        preprocess_malware_dataset(malware_input, malware_output)
