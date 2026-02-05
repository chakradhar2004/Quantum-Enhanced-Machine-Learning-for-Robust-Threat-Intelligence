"""
Phase 3 - Domain Dataset Preprocessing
Reduce high-dimensional domain features to 4 principal components using PCA.
Input: data/domains/processed/domain_features.csv
Output: phase3/domain/domain_pca.csv
"""

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os

def preprocess_domain():
    """Load domain features and reduce dimensions using PCA."""
    
    # Define paths
    input_path = '..\\..\\data\\domains\\processed\\domain_features.csv'
    output_path = 'domain_pca.csv'
    
    print("[INFO] Loading domain features...")
    df = pd.read_csv(input_path)
    
    print(f"[INFO] Original shape: {df.shape}")
    print(f"[INFO] Columns: {df.columns.tolist()}")
    
    # Separate features and labels
    X = df.drop(columns='label').values
    y = df['label'].values
    
    print(f"[INFO] Feature shape: {X.shape}, Label shape: {y.shape}")
    
    # Standardize features before PCA
    print("[INFO] Standardizing features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Apply PCA to reduce to 4 components
    print("[INFO] Applying PCA (4 components)...")
    pca = PCA(n_components=4)
    X_reduced = pca.fit_transform(X_scaled)
    
    print(f"[INFO] Explained variance ratio: {pca.explained_variance_ratio_}")
    print(f"[INFO] Total variance explained: {sum(pca.explained_variance_ratio_):.4f}")
    
    # Create DataFrame with reduced features
    df_pca = pd.DataFrame(
        X_reduced,
        columns=[f'pc{i}' for i in range(1, 5)]
    )
    df_pca['label'] = y
    
    # Save to CSV
    df_pca.to_csv(output_path, index=False)
    print(f"[SUCCESS] Domain PCA data saved to {output_path}")
    print(f"[INFO] Output shape: {df_pca.shape}")
    
    return df_pca


if __name__ == "__main__":
    preprocess_domain()
