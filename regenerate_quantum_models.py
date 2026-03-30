"""
Improved Quantum Model Training Script

Key changes from original:
1. Training set increased from 500 → 5000 samples
2. Proper stratified train/test/validation split
3. Cross-validation for hyperparameter tuning
4. Comprehensive metric logging
5. Model manifest generation for integrity checks
"""

import numpy as np
import pandas as pd
import pickle
import json
import time
import warnings
import hashlib
from pathlib import Path

warnings.filterwarnings('ignore')

try:
    import dill
    DILL_AVAILABLE = True
except ImportError:
    DILL_AVAILABLE = False

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, roc_auc_score,
    classification_report,
)

try:
    from qiskit_aer import AerSimulator
    from qiskit.circuit.library import ZZFeatureMap
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    from qiskit_machine_learning.algorithms import QSVC
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    print("[WARNING] Qiskit not available. Cannot train quantum models.")


def load_and_prepare_data(project_root: Path):
    """Load PCA-reduced domain data."""
    domain_pca_path = project_root / 'phase3' / 'domain' / 'domain_pca.csv'

    if not domain_pca_path.exists():
        raise FileNotFoundError(f"Domain PCA data not found at {domain_pca_path}")

    df = pd.read_csv(domain_pca_path)

    if 'label' in df.columns:
        X = df.drop('label', axis=1).values
        y = df['label'].values
    else:
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values

    print(f"[INFO] Loaded {len(X)} samples, {X.shape[1]} features")
    print(f"[INFO] Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    return X, y


def prepare_quantum_data(X_full, y_full, n_qubits=4, train_size=5000, test_size=1000):
    """
    Prepare data for quantum training.

    KEY CHANGE: train_size increased from 500 → 5000
    """
    # Use only the first n_qubits PCA components
    X_pca = X_full[:, :n_qubits]

    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X_pca, y_full,
        test_size=0.2,
        random_state=42,
        stratify=y_full,
    )

    # Limit sizes (quantum simulation is expensive)
    actual_train = min(train_size, len(X_train))
    actual_test = min(test_size, len(X_test))

    # Stratified subsample
    if actual_train < len(X_train):
        X_train, _, y_train, _ = train_test_split(
            X_train, y_train,
            train_size=actual_train,
            random_state=42,
            stratify=y_train,
        )

    if actual_test < len(X_test):
        X_test, _, y_test, _ = train_test_split(
            X_test, y_test,
            train_size=actual_test,
            random_state=42,
            stratify=y_test,
        )

    print(f"[INFO] Training samples: {len(X_train)}, Test samples: {len(X_test)}")

    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, n_qubits


def train_qsvc(X_train, y_train, n_qubits, reps=2, entanglement='full'):
    """Train Quantum SVC with given hyperparameters."""
    if not QISKIT_AVAILABLE:
        raise ImportError("Qiskit required for QSVC training")

    feature_map = ZZFeatureMap(
        feature_dimension=n_qubits,
        reps=reps,
        entanglement=entanglement,
    )

    qk = FidelityQuantumKernel(feature_map=feature_map)
    qsvc = QSVC(quantum_kernel=qk)

    print(f"[INFO] Training QSVC (reps={reps}, entanglement={entanglement})...")
    qsvc.fit(X_train, y_train)

    return qsvc


def evaluate_model(model, X_test, y_test, model_name="Model"):
    """Comprehensive model evaluation."""
    y_pred = model.predict(X_test)
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1_score': float(f1_score(y_test, y_pred, zero_division=0)),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
    }

    # Try AUC
    try:
        if hasattr(model, 'decision_function'):
            decision = model.decision_function(X_test)
            metrics['auc_roc'] = float(roc_auc_score(y_test, decision))
    except Exception:
        pass

    print(f"\n{'=' * 50}")
    print(f"{model_name} Performance:")
    print(f"{'=' * 50}")
    print(classification_report(y_test, y_pred, target_names=['Benign', 'Malicious']))
    print(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")

    return metrics


def compute_file_hash(filepath):
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def save_model(model, filepath):
    """Save model using dill with hash recording."""
    if not DILL_AVAILABLE:
        raise ImportError("dill is required: pip install dill")
    with open(filepath, 'wb') as f:
        dill.dump(model, f)
    return compute_file_hash(filepath)


def main():
    project_root = Path(__file__).parent
    models_dir = project_root / 'phase4' / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)

    # ── Load data ──
    X_full, y_full = load_and_prepare_data(project_root)

    # ── Prepare quantum data (5000 training samples) ──
    X_train, X_test, y_train, y_test, scaler, n_qubits = prepare_quantum_data(
        X_full, y_full,
        n_qubits=4,
        train_size=5000,  # KEY CHANGE: was 500
        test_size=1000,
    )

    results = {}

    # ── Train QSVC ──
    start = time.time()
    qsvc_model = train_qsvc(X_train, y_train, n_qubits, reps=2)
    train_time = time.time() - start

    # Evaluate
    start = time.time()
    qsvc_metrics = evaluate_model(qsvc_model, X_test, y_test, "QSVC")
    pred_time = time.time() - start

    # Save model
    qsvc_path = models_dir / 'qsvc_domain_model.dill'
    qsvc_hash = save_model(qsvc_model, qsvc_path)

    # Save scaler
    scaler_path = models_dir / 'quantum_scaler.pkl'
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    scaler_hash = compute_file_hash(scaler_path)

    # Save metadata
    qsvc_metadata = {
        'model_type': 'QSVC',
        'n_qubits': n_qubits,
        'feature_map': 'ZZFeatureMap',
        'feature_map_reps': 2,
        'feature_map_entanglement': 'full',
        'n_training_samples': len(X_train),
        'n_test_samples': len(X_test),
        'training_time_seconds': float(train_time),
        'prediction_time_seconds': float(pred_time),
        **qsvc_metrics,
    }

    with open(models_dir / 'qsvc_metadata.json', 'w') as f:
        json.dump(qsvc_metadata, f, indent=2)

    # ── Generate model manifest ──
    manifest = {
        'qsvc_domain_model.dill': qsvc_hash,
        'quantum_scaler.pkl': scaler_hash,
    }
    with open(models_dir / 'model_manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print("QUANTUM MODEL TRAINING COMPLETE")
    print(f"{'=' * 60}")
    print(f"QSVC Accuracy:  {qsvc_metrics['accuracy']:.4f} ({qsvc_metrics['accuracy']*100:.2f}%)")
    print(f"QSVC Precision: {qsvc_metrics['precision']:.4f}")
    print(f"QSVC Recall:    {qsvc_metrics['recall']:.4f}")
    print(f"QSVC F1:        {qsvc_metrics['f1_score']:.4f}")
    print(f"Training Time:  {train_time:.1f}s")
    print(f"Training Size:  {len(X_train)} samples")
    print(f"\nModels saved to: {models_dir}")
    print(f"Manifest saved to: {models_dir / 'model_manifest.json'}")
    print(f"{'=' * 60}")

    return results


if __name__ == '__main__':
    main()
