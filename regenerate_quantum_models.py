"""
Clean quantum model regeneration script.
No print statements or tabs are allowed during model saving.
This ensures the pickled models are clean and can be loaded without errors.
"""

import numpy as np
import pandas as pd
import pickle
import json
import time
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

try:
    import dill
    DILL_AVAILABLE = True
except ImportError:
    DILL_AVAILABLE = False

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from qiskit_aer import AerSimulator
from qiskit.circuit.library import ZZFeatureMap
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.algorithms import QSVC


def load_and_prepare_data():
    project_root = Path(__file__).parent
    phase3_dir = project_root / 'phase3'
    domain_pca_path = phase3_dir / 'domain' / 'domain_pca.csv'
    
    if not domain_pca_path.exists():
        raise FileNotFoundError(f"Domain PCA data not found at {domain_pca_path}")
    
    domain_pca_df = pd.read_csv(domain_pca_path)
    
    if 'label' in domain_pca_df.columns:
        X_domain_full = domain_pca_df.drop('label', axis=1).values
        y_domain = domain_pca_df['label'].values
    else:
        X_domain_full = domain_pca_df.iloc[:, :-1].values
        y_domain = domain_pca_df.iloc[:, -1].values
    
    return X_domain_full, y_domain


def prepare_quantum_data(X_domain_full, y_domain):
    n_qubits = 4
    X_domain_pca = X_domain_full[:, :n_qubits]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_domain_pca, y_domain,
        test_size=0.2,
        random_state=42,
        stratify=y_domain
    )
    
    # Use larger subset for better QML training
    train_size = min(500, len(X_train))
    test_size = min(150, len(X_test))
    
    X_train_q = X_train[:train_size]
    y_train_q = y_train[:train_size]
    X_test_q = X_test[:test_size]
    y_test_q = y_test[:test_size]
    
    # Scale using StandardScaler
    scaler = StandardScaler()
    X_train_q_scaled = scaler.fit_transform(X_train_q)
    X_test_q_scaled = scaler.transform(X_test_q)
    
    return X_train_q_scaled, X_test_q_scaled, y_train_q, y_test_q, scaler, n_qubits


def train_qsvc(X_train_scaled, y_train, n_qubits):
    # Create feature map
    feature_map = ZZFeatureMap(feature_dimension=n_qubits, reps=2, entanglement='full')
    
    # Create quantum kernel
    backend = AerSimulator()
    qk = FidelityQuantumKernel(feature_map=feature_map)
    
    # Train QSVC
    qsvc = QSVC(quantum_kernel=qk)
    qsvc.fit(X_train_scaled, y_train)
    
    return qsvc


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    return {
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'confusion_matrix': cm.tolist()
    }


def save_model_clean(model, filepath):
    if not DILL_AVAILABLE:
        raise ImportError("dill is required to save quantum models")
    
    with open(filepath, 'wb') as f:
        dill.dump(model, f)


def save_scaler_clean(scaler, filepath):
    with open(filepath, 'wb') as f:
        pickle.dump(scaler, f)


def save_metadata_clean(metadata, filepath):
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)


def main():
    # Set paths
    project_root = Path(__file__).parent
    phase4_dir = project_root / 'phase4'
    models_dir = phase4_dir / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and prepare data
    X_domain_full, y_domain = load_and_prepare_data()
    X_train_q_scaled, X_test_q_scaled, y_train_q, y_test_q, scaler, n_qubits = prepare_quantum_data(
        X_domain_full, y_domain
    )
    
    # Train QSVC
    start_time = time.time()
    qsvc_model = train_qsvc(X_train_q_scaled, y_train_q, n_qubits)
    training_time = time.time() - start_time
    
    # Evaluate QSVC
    start_time = time.time()
    qsvc_metrics = evaluate_model(qsvc_model, X_test_q_scaled, y_test_q)
    prediction_time = time.time() - start_time
    
    # Save QSVC model CLEAN (no print statements during saving)
    qsvc_model_path = models_dir / 'qsvc_domain_model.dill'
    save_model_clean(qsvc_model, qsvc_model_path)
    
    # Save scaler CLEAN
    scaler_path = models_dir / 'quantum_scaler.pkl'
    save_scaler_clean(scaler, scaler_path)
    
    # Save metadata CLEAN
    qsvc_metadata = {
        'model_type': 'QSVC',
        'n_qubits': n_qubits,
        'feature_map': 'ZZFeatureMap',
        'feature_map_reps': 2,
        'feature_map_entanglement': 'full',
        'n_training_samples': len(X_train_q_scaled),
        'n_test_samples': len(X_test_q_scaled),
        'accuracy': float(qsvc_metrics['accuracy']),
        'precision': float(qsvc_metrics['precision']),
        'recall': float(qsvc_metrics['recall']),
        'f1_score': float(qsvc_metrics['f1_score']),
        'training_time_seconds': float(training_time),
        'prediction_time_seconds': float(prediction_time),
    }
    
    qsvc_metadata_path = models_dir / 'qsvc_metadata.json'
    save_metadata_clean(qsvc_metadata, qsvc_metadata_path)
    
    # Return results (no prints during main execution)
    return {
        'qsvc_model_path': str(qsvc_model_path),
        'scaler_path': str(scaler_path),
        'metadata_path': str(qsvc_metadata_path),
        'metrics': qsvc_metrics,
        'training_time': training_time,
        'prediction_time': prediction_time
    }


if __name__ == '__main__':
    results = main()
    print("QUANTUM MODELS REGENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"QSVC Model: {results['qsvc_model_path']}")
    print(f"Scaler: {results['scaler_path']}")
    print(f"Metadata: {results['metadata_path']}")
    print()
    print("QSVC PERFORMANCE:")
    print(f"  Accuracy:  {results['metrics']['accuracy']:.4f} ({results['metrics']['accuracy']*100:.2f}%)")
    print(f"  Precision: {results['metrics']['precision']:.4f}")
    print(f"  Recall:    {results['metrics']['recall']:.4f}")
    print(f"  F1 Score:  {results['metrics']['f1_score']:.4f}")
    print()
    print(f"Training Time: {results['training_time']:.2f}s")
    print(f"Prediction Time: {results['prediction_time']:.2f}s")
    print("=" * 60)
