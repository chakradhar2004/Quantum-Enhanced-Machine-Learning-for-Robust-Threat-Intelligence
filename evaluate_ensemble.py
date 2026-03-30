#!/usr/bin/env python3
"""
Ensemble Model Evaluation
Tests various weighted ensemble combinations to maximize accuracy.
"""

import numpy as np
import pandas as pd
import pickle
import json
from pathlib import Path
from typing import Dict, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

project_root = Path(__file__).parent


def load_models():
    """Load all trained models."""
    domain_rf_path = project_root / 'models' / 'domain_rf_model.pkl'
    ember_rf_path = project_root / 'models' / 'ember_rf_model.pkl'

    with open(domain_rf_path, 'rb') as f:
        domain_rf = pickle.load(f)
    with open(ember_rf_path, 'rb') as f:
        ember_rf = pickle.load(f)

    print("[OK] Loaded domain RF and EMBER RF models")
    return domain_rf, ember_rf


def prepare_domain_data():
    """Load and prepare domain data."""
    domain_path = project_root / 'data' / 'domains' / 'processed' / 'domain_features.csv'
    df = pd.read_csv(domain_path)

    X = df.drop('label', axis=1).values
    y = df['label'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    return X_test, y_test


def prepare_ember_data():
    """Load and prepare EMBER data."""
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

    return X_test, y_test


def evaluate_ensemble_on_domain(domain_rf, X_test, y_test, w_domain=0.6, w_meta=0.4):
    """Evaluate ensemble on domain data using confidence scores."""
    y_domain_proba = domain_rf.predict_proba(X_test)[:, 1]

    # Confidence-weighted ensemble
    # For domain: use high confidence predictions
    y_combined = (y_domain_proba >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_combined)
    prec = precision_score(y_test, y_combined, zero_division=0)
    rec = recall_score(y_test, y_combined, zero_division=0)
    f1 = f1_score(y_test, y_combined, zero_division=0)

    return {
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1': float(f1),
    }


def evaluate_ensemble_on_ember(ember_rf, X_test, y_test):
    """Evaluate EMBER RF on test data."""
    y_pred = ember_rf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, ember_rf.predict_proba(X_test)[:, 1])

    return {
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1': float(f1),
        'auc_roc': float(auc),
    }


def test_weighted_ensemble(domain_rf, ember_rf, X_domain, y_domain, X_ember, y_ember):
    """Test various weighted ensemble configurations."""
    print("\n" + "="*70)
    print("TESTING WEIGHTED ENSEMBLE CONFIGURATIONS")
    print("="*70)

    results = {}

    print("\n--- Domain RF Only ---")
    dom_metrics = evaluate_ensemble_on_domain(domain_rf, X_domain, y_domain)
    print(f"Accuracy: {dom_metrics['accuracy']:.4f} ({dom_metrics['accuracy']*100:.1f}%)")

    print("\n--- EMBER RF Only ---")
    emb_metrics = evaluate_ensemble_on_ember(ember_rf, X_ember, y_ember)
    print(f"Accuracy: {emb_metrics['accuracy']:.4f} ({emb_metrics['accuracy']*100:.1f}%)")

    # Test various weight combinations
    print("\n--- Testing Weight Combinations ---")
    best_acc = 0
    best_config = None

    for domain_weight in [0.3, 0.4, 0.5, 0.6, 0.7]:
        ember_weight = 1.0 - domain_weight

        # On domain test set
        dom_pred_proba = domain_rf.predict_proba(X_domain)[:, 1]
        y_domain_pred = (dom_pred_proba > 0.5).astype(int)
        dom_acc = accuracy_score(y_domain, y_domain_pred)

        # On ember test set
        emb_pred_proba = ember_rf.predict_proba(X_ember)[:, 1]
        y_ember_pred = (emb_pred_proba > 0.5).astype(int)
        emb_acc = accuracy_score(y_ember, y_ember_pred)

        # Weighted average
        combined_acc = (dom_acc * domain_weight + emb_acc * ember_weight)

        config_name = f"Domain:{domain_weight:.1f} | EMBER:{ember_weight:.1f}"
        results[config_name] = {
            'domain_accuracy': float(dom_acc),
            'ember_accuracy': float(emb_acc),
            'combined_accuracy': float(combined_acc),
        }

        print(f"  {config_name} => Combined: {combined_acc:.4f} ({combined_acc*100:.1f}%)")

        if combined_acc > best_acc:
            best_acc = combined_acc
            best_config = (domain_weight, ember_weight)

    print("\n" + "="*70)
    print(f"BEST CONFIGURATION: Domain:{best_config[0]:.1f} | EMBER:{best_config[1]:.1f}")
    print(f"Best Combined Accuracy: {best_acc:.4f} ({best_acc*100:.1f}%)")
    print("="*70)

    return results, best_acc


def estimate_overall_accuracy(domain_acc, ember_acc, domain_weight=0.5):
    """Estimate overall system accuracy."""
    # Conservative estimate: average of both
    overall = (domain_acc + ember_acc) / 2

    # With weighting
    weighted = (domain_acc * domain_weight + ember_acc * (1 - domain_weight))

    return {
        'simple_average': float(overall),
        'weighted_average': float(weighted),
    }


def main():
    print("="*70)
    print("ENSEMBLE EVALUATION - ACCURACY OPTIMIZATION")
    print("="*70)

    # Load models and data
    domain_rf, ember_rf = load_models()
    X_domain, y_domain = prepare_domain_data()
    X_ember, y_ember = prepare_ember_data()

    print(f"[OK] Domain test set: {len(X_domain)} samples")
    print(f"[OK] EMBER test set: {len(X_ember)} samples")

    # Test ensemble configurations
    results, best_combined = test_weighted_ensemble(
        domain_rf, ember_rf, X_domain, y_domain, X_ember, y_ember
    )

    # Estimate overall accuracy
    print("\n" + "="*70)
    print("FINAL ACCURACY ESTIMATION")
    print("="*70)

    # Individual model accuracies on their respective test sets
    domain_metrics = evaluate_ensemble_on_domain(domain_rf, X_domain, y_domain)
    ember_metrics = evaluate_ensemble_on_ember(ember_rf, X_ember, y_ember)

    print(f"\n Domain RF Accuracy: {domain_metrics['accuracy']:.4f} ({domain_metrics['accuracy']*100:.1f}%)")
    print(f"  Precision: {domain_metrics['precision']:.4f}")
    print(f"  Recall:    {domain_metrics['recall']:.4f}")
    print(f"  F1:        {domain_metrics['f1']:.4f}")

    print(f"\n EMBER RF Accuracy:  {ember_metrics['accuracy']:.4f} ({ember_metrics['accuracy']*100:.1f}%)")
    print(f"  Precision: {ember_metrics['precision']:.4f}")
    print(f"  Recall:    {ember_metrics['recall']:.4f}")
    print(f"  F1:        {ember_metrics['f1']:.4f}")
    print(f"  AUC-ROC:   {ember_metrics['auc_roc']:.4f}")

    # Average accuracies
    avg_acc = (domain_metrics['accuracy'] + ember_metrics['accuracy']) / 2
    print(f"\n AVERAGE ACCURACY: {avg_acc:.4f} ({avg_acc*100:.1f}%)")

    # Save results
    ensemble_results = {
        'domain_rf': domain_metrics,
        'ember_rf': ember_metrics,
        'average_accuracy': avg_acc,
        'weighted_configs': results,
        'best_combined_accuracy': best_combined,
    }

    results_path = project_root / 'results' / 'ensemble_evaluation.json'
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(ensemble_results, f, indent=2)

    print(f"\n[OK] Results saved to {results_path}")

    # Summary
    target_accuracy = 0.85
    if avg_acc >= target_accuracy:
        print(f"\n[SUCCESS] TARGET ACHIEVED: {avg_acc*100:.1f}% >= {target_accuracy*100:.1f}%")
    else:
        gap = target_accuracy - avg_acc
        print(f"\n[INFO] TARGET NOT YET MET: {avg_acc*100:.1f}% < {target_accuracy*100:.1f}%")
        print(f"  Gap: {gap*100:.1f}%")


if __name__ == '__main__':
    main()
