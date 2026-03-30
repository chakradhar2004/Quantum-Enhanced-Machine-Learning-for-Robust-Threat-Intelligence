"""
Model Accuracy Evaluation Script
Tests all trained models on their respective datasets.
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
    roc_auc_score,
)

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def evaluate_domain_rf():
    """Evaluate Domain Random Forest model."""
    print("\n" + "=" * 70)
    print("1. DOMAIN RANDOM FOREST MODEL")
    print("=" * 70)

    model_path = project_root / 'models' / 'domain_rf_model.pkl'
    if not model_path.exists():
        print("[SKIP] Domain RF model not found")
        return None

    import pickle
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print(f"[OK] Loaded model from {model_path}")
    n_expected = model.n_features_in_ if hasattr(model, 'n_features_in_') else None
    print(f"[OK] Model expects {n_expected} features")

    # Try PCA data (matches original training pipeline)
    pca_path = project_root / 'phase3' / 'domain' / 'domain_pca.csv'
    raw_path = project_root / 'data' / 'domains' / 'processed' / 'domain_features.csv'

    for dp in [raw_path, pca_path]:
        if dp.exists():
            df = pd.read_csv(dp)
            print(f"[OK] Loaded {len(df)} samples from {dp.name}")
            break
    else:
        print("[SKIP] No domain data found")
        return None

    if 'label' in df.columns:
        X = df.drop(columns='label').values
        y = df['label'].values
    else:
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values

    # Trim features to match model
    if n_expected and X.shape[1] > n_expected:
        print(f"[INFO] Trimming features {X.shape[1]} -> {n_expected}")
        X = X[:, :n_expected]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[OK] Train: {len(X_train)}, Test: {len(X_test)}")
    print(f"[OK] Class dist (test): {dict(zip(*np.unique(y_test, return_counts=True)))}")

    y_pred = model.predict(X_test)
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
    }
    try:
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics['auc_roc'] = float(roc_auc_score(y_test, y_proba))
    except Exception:
        pass

    print(f"\n{classification_report(y_test, y_pred, target_names=['Benign (0)', 'Malicious (1)'])}")
    print(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
    if 'auc_roc' in metrics:
        print(f"AUC-ROC: {metrics['auc_roc']:.4f}")
    return metrics


def evaluate_ember_rf():
    """Evaluate EMBER Random Forest model."""
    print("\n" + "=" * 70)
    print("2. EMBER (MALWARE) RANDOM FOREST MODEL")
    print("=" * 70)

    model_path = project_root / 'models' / 'ember_rf_model.pkl'
    if not model_path.exists():
        print("[SKIP] EMBER RF model not found")
        return None

    import pickle
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print(f"[OK] Loaded model")

    n_expected = model.n_features_in_ if hasattr(model, 'n_features_in_') else None
    feature_names = list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else None
    print(f"[OK] Model expects {n_expected} features")
    if feature_names:
        print(f"[OK] Feature names: {feature_names}")

    data_path = project_root / 'data' / 'malware' / 'processed' / 'ember_features.csv'
    if not data_path.exists():
        print("[SKIP] EMBER features data not found")
        return None

    df = pd.read_csv(data_path)
    print(f"[OK] Loaded {len(df)} samples, columns: {list(df.columns)}")

    # One-hot encode 'machine' column to match training
    if 'machine' in df.columns:
        machine_dummies = pd.get_dummies(df['machine'], prefix='machine')
        df = df.drop(columns='machine')
        df = pd.concat([df, machine_dummies], axis=1)
        print(f"[OK] One-hot encoded 'machine' -> {list(machine_dummies.columns)}")

    # Separate label
    y = df['label'].values
    X_df = df.drop(columns='label')

    # Align columns with model's expected feature names
    if feature_names:
        # Add missing columns as 0
        for col in feature_names:
            if col not in X_df.columns:
                X_df[col] = 0
        # Select only expected columns in correct order
        X_df = X_df[feature_names]
        print(f"[OK] Aligned to {len(feature_names)} features matching model")

    X = X_df.values.astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[OK] Train: {len(X_train)}, Test: {len(X_test)}")
    print(f"[OK] Class dist (test): {dict(zip(*np.unique(y_test, return_counts=True)))}")

    y_pred = model.predict(X_test)
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
    }
    try:
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics['auc_roc'] = float(roc_auc_score(y_test, y_proba))
    except Exception:
        pass

    print(f"\n{classification_report(y_test, y_pred, target_names=['Benign (0)', 'Malware (1)'])}")
    print(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
    if 'auc_roc' in metrics:
        print(f"AUC-ROC: {metrics['auc_roc']:.4f}")
    return metrics


def evaluate_qsvc_metadata():
    """Report QSVC metrics from training metadata."""
    print("\n" + "=" * 70)
    print("3. QUANTUM SVC (QSVC) — TRAINING METADATA")
    print("=" * 70)

    meta_path = project_root / 'phase4' / 'models' / 'qsvc_metadata.json'
    if not meta_path.exists():
        print("[SKIP] QSVC metadata not found")
        return None

    with open(meta_path) as f:
        meta = json.load(f)

    print(f"  Model:            {meta.get('model_type')}")
    print(f"  Qubits:           {meta.get('n_qubits')}")
    print(f"  Feature map:      {meta.get('feature_map')} (reps={meta.get('feature_map_reps')})")
    print(f"  Training samples: {meta.get('n_training_samples')}")
    print(f"  Test samples:     {meta.get('n_test_samples')}")
    print(f"  " + "-" * 37)
    print(f"  Accuracy:         {meta.get('accuracy', 0):.4f}  ({meta.get('accuracy', 0)*100:.1f}%)")
    print(f"  Precision:        {meta.get('precision', 0):.4f}")
    print(f"  Recall:           {meta.get('recall', 0):.4f}")
    print(f"  F1 Score:         {meta.get('f1_score', 0):.4f}")
    print(f"  Training time:    {meta.get('training_time_seconds', 0):.1f}s")

    return {
        'accuracy': meta.get('accuracy', 0),
        'precision': meta.get('precision', 0),
        'recall': meta.get('recall', 0),
        'f1': meta.get('f1_score', 0),
        'training_samples': meta.get('n_training_samples'),
    }


def evaluate_vqc_metadata():
    """Report VQC metrics from training metadata."""
    print("\n" + "=" * 70)
    print("4. VARIATIONAL QUANTUM CLASSIFIER (VQC) — TRAINING METADATA")
    print("=" * 70)

    meta_path = project_root / 'phase4' / 'models' / 'vqc_metadata.json'
    if not meta_path.exists():
        print("[SKIP] VQC metadata not found")
        return None

    with open(meta_path) as f:
        meta = json.load(f)

    print(f"  Model:            {meta.get('model_type')}")
    print(f"  Qubits:           {meta.get('n_qubits')}")
    print(f"  Feature map:      {meta.get('feature_map')} (reps={meta.get('feature_map_reps')})")
    print(f"  Ansatz:           {meta.get('ansatz')} (reps={meta.get('ansatz_reps')})")
    print(f"  Training samples: {meta.get('train_samples')}")
    print(f"  Test samples:     {meta.get('test_samples')}")
    print(f"  " + "-" * 37)
    print(f"  Accuracy:         {meta.get('accuracy', 0):.4f}  ({meta.get('accuracy', 0)*100:.1f}%)")
    print(f"  Precision:        {meta.get('precision', 0):.4f}")
    print(f"  Recall:           {meta.get('recall', 0):.4f}")
    print(f"  F1 Score:         {meta.get('f1_score', 0):.4f}")
    print(f"  Training time:    {meta.get('training_time_seconds', 0):.1f}s")
    imp = meta.get('improvement_over_qsvc', 0)
    print(f"  vs QSVC:          {imp:+.1f}% {'[WORSE]' if imp < 0 else '[BETTER]'}")

    return {
        'accuracy': meta.get('accuracy', 0),
        'precision': meta.get('precision', 0),
        'recall': meta.get('recall', 0),
        'f1': meta.get('f1_score', 0),
        'training_samples': meta.get('train_samples'),
    }


def main():
    print("=" * 70)
    print("  QUANTUM-ENHANCED THREAT INTELLIGENCE — ACCURACY EVALUATION")
    print("=" * 70)

    all_results = {}

    r = evaluate_domain_rf()
    if r: all_results['Domain RF'] = r

    r = evaluate_ember_rf()
    if r: all_results['EMBER RF'] = r

    r = evaluate_qsvc_metadata()
    if r: all_results['QSVC (quantum)'] = r

    r = evaluate_vqc_metadata()
    if r: all_results['VQC (quantum)'] = r

    # ── Summary Table ──
    print("\n" + "=" * 70)
    print("  FINAL ACCURACY SUMMARY")
    print("=" * 70)
    print(f"\n  {'Model':<20} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'AUC-ROC':>10}")
    print("  " + "-" * 70)

    for name, m in all_results.items():
        auc = f"{m['auc_roc']:.4f}" if 'auc_roc' in m else "  N/A"
        samples = f" ({m['training_samples']} train)" if 'training_samples' in m else ""
        print(f"  {name:<20} {m['accuracy']:>10.4f} {m['precision']:>10.4f} "
              f"{m['recall']:>10.4f} {m['f1']:>10.4f} {auc:>10}{samples}")

    print("\n" + "=" * 70)

    # Save
    output_path = project_root / 'results' / 'accuracy_evaluation.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"  Results saved to: {output_path}\n")


if __name__ == '__main__':
    main()
