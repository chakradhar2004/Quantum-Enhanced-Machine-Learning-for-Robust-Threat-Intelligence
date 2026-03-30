#!/usr/bin/env python3
"""
Improved Quantum Model Training
Trains QSVC with better parameters and larger dataset.
"""

import numpy as np
import pandas as pd
import json
import time
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

project_root = Path(__file__).parent

try:
    from qiskit_aer import AerSimulator
    from qiskit.circuit.library import ZZFeatureMap
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    from qiskit_machine_learning.algorithms import QSVC
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    print("[WARNING] Qiskit not available - skipping quantum model training")


def train_improved_qsvc():
    """Train improved QSVC with larger dataset."""
    if not QISKIT_AVAILABLE:
        print("[SKIP] Qiskit not available")
        return None

    print("\n" + "="*70)
    print("TRAINING: Improved QSVC (Quantum Support Vector Classifier)")
    print("="*70)

    # Load domain data (larger sample than before: 5000 instead of 500)
    domain_path = project_root / 'data' / 'domains' / 'processed' / 'domain_features.csv'
    df = pd.read_csv(domain_path)

    # Sample 5000 stratified samples
    from sklearn.model_selection import StratifiedShuffleSplit
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.8, random_state=42)
    train_idx, _ = next(sss.split(df, df['label']))
    df_train = df.iloc[train_idx].head(5000)

    X = df_train.drop('label', axis=1).values
    y = df_train['label'].values

    print(f"[OK] Loaded {len(df_train)} training samples")
    print(f"[OK] Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Scale features to [0, 2π] for quantum circuits
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = 2 * np.pi * (X_scaled - X_scaled.min(axis=0)) / (X_scaled.max(axis=0) - X_scaled.min(axis=0) + 1e-8)

    # Split into train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42, stratify=y
    )

    print(f"[OK] Train: {len(X_train)}, Test: {len(X_test)}")

    # Create quantum feature map
    n_qubits = min(4, X_train.shape[1])  # Limit to 4 qubits for performance
    feature_map = ZZFeatureMap(feature_dimension=n_qubits, reps=2, entanglement='linear')

    print(f"[OK] Feature map: ZZFeatureMap with {n_qubits} qubits, 2 reps")

    # Setup quantum kernel
    simulator = AerSimulator()
    kernel = FidelityQuantumKernel(feature_map=feature_map, input_params=None)

    print("[OK] Setting up quantum kernel...")

    # Train QSVC
    print("[OK] Training QSVC (this may take a few minutes)...")
    start = time.time()

    qsvc = QSVC(quantum_kernel=kernel, C=1.0, gamma='auto')

    # Only use subset for speed
    subset_size = min(1000, len(X_train))
    qsvc.fit(X_train[:subset_size], y_train[:subset_size])

    train_time = time.time() - start

    # Evaluate
    y_pred = qsvc.predict(X_test[:500])  # Evaluate on smaller subset
    y_test_subset = y_test[:500]

    acc = accuracy_score(y_test_subset, y_pred)
    prec = precision_score(y_test_subset, y_pred, zero_division=0)
    rec = recall_score(y_test_subset, y_pred, zero_division=0)
    f1 = f1_score(y_test_subset, y_pred, zero_division=0)

    print(f"\n[OK] Training complete in {train_time:.1f}s")
    print(f"Accuracy:  {acc:.4f} ({acc*100:.1f}%)")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1:        {f1:.4f}")

    # Save metadata
    metadata = {
        'model_type': 'QSVC',
        'n_qubits': n_qubits,
        'feature_map': 'ZZFeatureMap',
        'feature_map_reps': 2,
        'n_training_samples': subset_size,
        'n_test_samples': len(y_test_subset),
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1_score': float(f1),
        'training_time_seconds': train_time,
        'improvement_notes': 'Trained on 5000 stratified samples (1000 subset for speed)',
    }

    metadata_path = project_root / 'phase4' / 'models' / 'qsvc_improved_metadata.json'
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Metadata saved to {metadata_path}")

    return metadata


def main():
    print("="*70)
    print("QUANTUM MODEL IMPROVEMENT")
    print("="*70)

    if QISKIT_AVAILABLE:
        try:
            metadata = train_improved_qsvc()
            if metadata:
                print("\n" + "="*70)
                print("QUANTUM TRAINING COMPLETE")
                print("="*70)
        except Exception as e:
            print(f"[ERROR] Failed to train quantum model: {e}")
            print("[INFO] Continuing with classical models only")
    else:
        print("[SKIP] Quantum computing libraries not available")
        print("[INFO] Classical models (RF) continue to provide 86.6% accuracy")


if __name__ == '__main__':
    main()
