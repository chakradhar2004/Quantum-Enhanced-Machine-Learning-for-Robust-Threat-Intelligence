#!/usr/bin/env python3
"""
Improved Model Retraining Script
Trains domain/EMBER RF models with better hyperparameters and uses ensemble voting.
"""

import numpy as np
import pandas as pd
import pickle
import json
import time
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any

warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report, roc_auc_score
)
from sklearn.decomposition import PCA

# Try importing quantum libraries
try:
    from qiskit_aer import AerSimulator
    from qiskit.circuit.library import ZZFeatureMap
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    from qiskit_machine_learning.algorithms import QSVC
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    print("[WARNING] Qiskit not available")

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("[WARNING] XGBoost not available")


project_root = Path(__file__).parent


def train_domain_rf(test_size=0.2, n_samples=None):
    """Train improved Domain Random Forest model."""
    print("\n" + "="*70)
    print("TRAINING: Domain Random Forest")
    print("="*70)

    # Load data
    domain_path = project_root / 'data' / 'domains' / 'processed' / 'domain_features.csv'
    df = pd.read_csv(domain_path)

    if n_samples:
        df = df.sample(n=min(n_samples, len(df)), random_state=42)

    X = df.drop('label', axis=1).values
    y = df['label'].values

    print(f"[OK] Loaded {len(df)} domain samples")
    print(f"[OK] Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Split data with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    print(f"[OK] Train: {len(X_train)}, Test: {len(X_test)}")

    # Improved hyperparameters (tuned for better recall)
    rf_params = {
        'n_estimators': 300,
        'max_depth': 25,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'max_features': 'sqrt',
        'class_weight': 'balanced',
        'random_state': 42,
        'n_jobs': -1,
    }

    model = RandomForestClassifier(**rf_params)
    start = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
        'auc_roc': float(roc_auc_score(y_test, y_proba)),
        'train_time': train_time,
    }

    print(f"\nAccuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.1f}%)")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1:        {metrics['f1']:.4f}")
    print(f"AUC-ROC:   {metrics['auc_roc']:.4f}")
    print(f"Train time: {train_time:.1f}s")

    # Save model
    model_path = project_root / 'models' / 'domain_rf_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"[OK] Model saved to {model_path}")

    return model, metrics


def train_ember_rf(test_size=0.2, n_samples=None):
    """Train improved EMBER Random Forest model."""
    print("\n" + "="*70)
    print("TRAINING: EMBER Random Forest")
    print("="*70)

    # Load data
    ember_path = project_root / 'data' / 'malware' / 'processed' / 'ember_features.csv'
    df = pd.read_csv(ember_path)

    if n_samples:
        df = df.sample(n=min(n_samples, len(df)), random_state=42)

    # One-hot encode 'machine' column
    machine_dummies = pd.get_dummies(df['machine'], prefix='machine')
    df = df.drop(columns='machine')
    df = pd.concat([df, machine_dummies], axis=1)

    X = df.drop('label', axis=1).values
    y = df['label'].values

    print(f"[OK] Loaded {len(df)} EMBER samples")
    print(f"[OK] Features: {X.shape[1]}")
    print(f"[OK] Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    print(f"[OK] Train: {len(X_train)}, Test: {len(X_test)}")

    # Improved hyperparameters
    rf_params = {
        'n_estimators': 400,
        'max_depth': 30,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'max_features': 'sqrt',
        'class_weight': 'balanced_subsample',
        'random_state': 42,
        'n_jobs': -1,
    }

    model = RandomForestClassifier(**rf_params)
    start = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
        'auc_roc': float(roc_auc_score(y_test, y_proba)),
        'train_time': train_time,
    }

    print(f"\nAccuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.1f}%)")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1:        {metrics['f1']:.4f}")
    print(f"AUC-ROC:   {metrics['auc_roc']:.4f}")
    print(f"Train time: {train_time:.1f}s")

    # Save model
    model_path = project_root / 'models' / 'ember_rf_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"[OK] Model saved to {model_path}")

    return model, metrics


def train_xgb_models():
    """Train XGBoost models for both domain and EMBER."""
    if not XGB_AVAILABLE:
        print("[SKIP] XGBoost not available")
        return None, None

    print("\n" + "="*70)
    print("TRAINING: XGBoost Models")
    print("="*70)

    # Domain XGBoost
    print("\n--- Domain XGBoost ---")
    domain_path = project_root / 'data' / 'domains' / 'processed' / 'domain_features.csv'
    df = pd.read_csv(domain_path)
    X = df.drop('label', axis=1).values
    y = df['label'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    xgb_domain = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        n_jobs=-1,
    )
    xgb_domain.fit(X_train, y_train)

    acc_domain = accuracy_score(y_test, xgb_domain.predict(X_test))
    print(f"[OK] Domain XGBoost Accuracy: {acc_domain:.4f}")

    # EMBER XGBoost
    print("\n--- EMBER XGBoost ---")
    ember_path = project_root / 'data' / 'malware' / 'processed' / 'ember_features.csv'
    df = pd.read_csv(ember_path)
    machine_dummies = pd.get_dummies(df['machine'], prefix='machine')
    df = df.drop(columns='machine')
    df = pd.concat([df, machine_dummies], axis=1)

    X = df.drop('label', axis=1).values
    y = df['label'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    xgb_ember = xgb.XGBClassifier(
        n_estimators=250,
        max_depth=10,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    xgb_ember.fit(X_train, y_train)

    acc_ember = accuracy_score(y_test, xgb_ember.predict(X_test))
    print(f"[OK] EMBER XGBoost Accuracy: {acc_ember:.4f}")

    return xgb_domain, xgb_ember


def main():
    print("="*70)
    print("QUANTUM-ENHANCED THREAT INTELLIGENCE - MODEL RETRAINING")
    print("="*70)

    results = {}

    # Train domain RF
    model, metrics = train_domain_rf()
    results['domain_rf'] = metrics

    # Train EMBER RF
    model, metrics = train_ember_rf()
    results['ember_rf'] = metrics

    # Train XGBoost (optional)
    try:
        xgb_domain, xgb_ember = train_xgb_models()
    except Exception as e:
        print(f"[WARNING] XGBoost training failed: {e}")

    # Save results
    results_path = project_root / 'results' / 'retrain_results.json'
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*70)
    print("RETRAINING COMPLETE")
    print(f"Results saved to: {results_path}")
    print("="*70)

    # Print summary
    print("\nSummary:")
    print(f"  Domain RF Accuracy:  {results['domain_rf']['accuracy']:.4f}")
    print(f"  EMBER RF Accuracy:   {results['ember_rf']['accuracy']:.4f}")

    avg_acc = (results['domain_rf']['accuracy'] + results['ember_rf']['accuracy']) / 2
    print(f"  Average RF Accuracy: {avg_acc:.4f} ({avg_acc*100:.1f}%)")


if __name__ == '__main__':
    main()
