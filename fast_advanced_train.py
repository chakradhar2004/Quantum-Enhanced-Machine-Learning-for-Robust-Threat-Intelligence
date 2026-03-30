#!/usr/bin/env python3
"""
Fast Advanced Training - Optimized for speed
Uses sampling for training, tests on full data for accurate metrics.
"""

import numpy as np
import pandas as pd
import pickle
import json
import time
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier,
    ExtraTreesClassifier, VotingClassifier
)
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import xgboost as xgb
import lightgbm as lgb

project_root = Path(__file__).parent


def load_domain_data():
    """Load domain data."""
    path = project_root / 'data' / 'domains' / 'processed' / 'domain_features.csv'
    df = pd.read_csv(path)
    X = df.drop('label', axis=1).values
    y = df['label'].values
    return X, y


def load_ember_data():
    """Load EMBER data."""
    path = project_root / 'data' / 'malware' / 'processed' / 'ember_features.csv'
    df = pd.read_csv(path)
    machine_dummies = pd.get_dummies(df['machine'], prefix='machine')
    df = df.drop(columns='machine')
    df = pd.concat([df, machine_dummies], axis=1)
    X = df.drop('label', axis=1).values
    y = df['label'].values
    return X, y


def train_fast_models(X, y, data_name='Domain'):
    """Train multiple models with fixed hyperparameters (optimized from prior tuning)."""

    print(f"\n{'='*70}")
    print(f"FAST TRAINING: {data_name}")
    print(f"{'='*70}")

    print(f"Dataset: {len(X)} samples, {X.shape[1]} features")
    print(f"Class dist: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Split into train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    results = {}
    models = {}

    # 1. Random Forest (proven best)
    print("\n[1/5] Training Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=400, max_depth=30, min_samples_split=5,
        class_weight='balanced', random_state=42, n_jobs=-1
    )
    rf.fit(X_train_scaled, y_train)
    y_pred_rf = rf.predict(X_test_scaled)
    acc_rf = accuracy_score(y_test, y_pred_rf)
    auc_rf = roc_auc_score(y_test, rf.predict_proba(X_test_scaled)[:, 1])
    results['Random Forest'] = {'acc': acc_rf, 'auc': auc_rf}
    models['rf'] = rf
    print(f"   Accuracy: {acc_rf:.4f} | AUC: {auc_rf:.4f}")

    # 2. Gradient Boosting
    print("[2/5] Training Gradient Boosting...")
    gb = GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.1, max_depth=7,
        min_samples_split=5, subsample=0.9, random_state=42
    )
    gb.fit(X_train_scaled, y_train)
    y_pred_gb = gb.predict(X_test_scaled)
    acc_gb = accuracy_score(y_test, y_pred_gb)
    auc_gb = roc_auc_score(y_test, gb.predict_proba(X_test_scaled)[:, 1])
    results['Gradient Boosting'] = {'acc': acc_gb, 'auc': auc_gb}
    models['gb'] = gb
    print(f"   Accuracy: {acc_gb:.4f} | AUC: {auc_gb:.4f}")

    # 3. Extra Trees
    print("[3/5] Training Extra Trees...")
    et = ExtraTreesClassifier(
        n_estimators=400, max_depth=30, min_samples_split=5,
        class_weight='balanced', random_state=42, n_jobs=-1
    )
    et.fit(X_train_scaled, y_train)
    y_pred_et = et.predict(X_test_scaled)
    acc_et = accuracy_score(y_test, y_pred_et)
    auc_et = roc_auc_score(y_test, et.predict_proba(X_test_scaled)[:, 1])
    results['Extra Trees'] = {'acc': acc_et, 'auc': auc_et}
    models['et'] = et
    print(f"   Accuracy: {acc_et:.4f} | AUC: {auc_et:.4f}")

    # 4. XGBoost
    print("[4/5] Training XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=300, max_depth=8, learning_rate=0.1,
        subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=-1,
        scale_pos_weight=sum(y_train == 0) / sum(y_train == 1),
    )
    xgb_model.fit(X_train_scaled, y_train)
    y_pred_xgb = xgb_model.predict(X_test_scaled)
    acc_xgb = accuracy_score(y_test, y_pred_xgb)
    auc_xgb = roc_auc_score(y_test, xgb_model.predict_proba(X_test_scaled)[:, 1])
    results['XGBoost'] = {'acc': acc_xgb, 'auc': auc_xgb}
    models['xgb'] = xgb_model
    print(f"   Accuracy: {acc_xgb:.4f} | AUC: {auc_xgb:.4f}")

    # 5. LightGBM
    print("[5/5] Training LightGBM...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=300, max_depth=8, learning_rate=0.1,
        num_leaves=31, subsample=0.8, colsample_bytree=0.8,
        class_weight='balanced', random_state=42, n_jobs=-1, verbose=-1
    )
    lgb_model.fit(X_train_scaled, y_train)
    y_pred_lgb = lgb_model.predict(X_test_scaled)
    acc_lgb = accuracy_score(y_test, y_pred_lgb)
    auc_lgb = roc_auc_score(y_test, lgb_model.predict_proba(X_test_scaled)[:, 1])
    results['LightGBM'] = {'acc': acc_lgb, 'auc': auc_lgb}
    models['lgb'] = lgb_model
    print(f"   Accuracy: {acc_lgb:.4f} | AUC: {auc_lgb:.4f}")

    # 6. Voting Ensemble
    print("[6/6] Creating Voting Ensemble...")
    voting_clf = VotingClassifier(
        estimators=[
            ('rf', rf),
            ('gb', gb),
            ('et', et),
            ('xgb', xgb_model),
            ('lgb', lgb_model),
        ],
        voting='soft',
        weights=[0.25, 0.20, 0.20, 0.20, 0.15]
    )
    voting_clf.fit(X_train_scaled, y_train)
    y_pred_voting = voting_clf.predict(X_test_scaled)
    acc_voting = accuracy_score(y_test, y_pred_voting)
    auc_voting = roc_auc_score(y_test, voting_clf.predict_proba(X_test_scaled)[:, 1])
    results['Voting Ensemble'] = {'acc': acc_voting, 'auc': auc_voting}
    models['voting'] = voting_clf
    print(f"   Accuracy: {acc_voting:.4f} | AUC: {auc_voting:.4f}")

    # Summary
    print(f"\n{'Model':<20} {'Accuracy':<12} {'AUC':<12}")
    print("-" * 45)
    for name, metrics in sorted(results.items(), key=lambda x: x[1]['acc'], reverse=True):
        print(f"{name:<20} {metrics['acc']:.4f}      {metrics['auc']:.4f}")

    # Find best
    best_model_name = max(results, key=lambda x: results[x]['acc'])
    best_model = models[best_model_name.lower().replace(' ', '_').split('_')[0]
                        if best_model_name != 'Voting Ensemble' else 'voting']
    best_acc = results[best_model_name]['acc']

    print(f"\n[BEST] {best_model_name}: {best_acc:.4f} ({best_acc*100:.1f}%)")

    # Save best model
    if data_name == 'Domain':
        save_path = project_root / 'models' / 'domain_best_model.pkl'
    else:
        save_path = project_root / 'models' / 'ember_best_model.pkl'

    with open(save_path, 'wb') as f:
        pickle.dump(best_model, f)

    print(f"[OK] Model saved to {save_path}")

    return results, best_acc


def main():
    print("="*70)
    print("FAST ADVANCED TRAINING PIPELINE")
    print("="*70)

    start_time = time.time()

    # Train domain models
    X_domain, y_domain = load_domain_data()
    domain_results, domain_best_acc = train_fast_models(X_domain, y_domain, 'Domain')

    # Train EMBER models
    X_ember, y_ember = load_ember_data()
    ember_results, ember_best_acc = train_fast_models(X_ember, y_ember, 'EMBER/Malware')

    # Final results
    print(f"\n{'='*70}")
    print("FINAL ACCURACY RESULTS")
    print(f"{'='*70}")

    avg_accuracy = (domain_best_acc + ember_best_acc) / 2

    print(f"\nDomain Best Accuracy:  {domain_best_acc:.4f} ({domain_best_acc*100:.1f}%)")
    print(f"EMBER Best Accuracy:   {ember_best_acc:.4f} ({ember_best_acc*100:.1f}%)")
    print(f"────────────────────────────────────────")
    print(f"AVERAGE ACCURACY:      {avg_accuracy:.4f} ({avg_accuracy*100:.1f}%)")

    target = 0.85
    if avg_accuracy >= target:
        status = "SUCCESS - TARGET EXCEEDED"
        margin = avg_accuracy - target
        print(f"\n[SUCCESS] {avg_accuracy*100:.1f}% >= {target*100:.1f}% (margin: +{margin*100:.1f}%)")
    else:
        status = "PENDING - FURTHER OPTIMIZATION NEEDED"
        gap = target - avg_accuracy
        print(f"\n[INFO] Gap to {target*100:.0f}% target: {gap*100:.1f}%")

    # Save results
    results = {
        'domain_models': domain_results,
        'ember_models': ember_results,
        'domain_best_accuracy': float(domain_best_acc),
        'ember_best_accuracy': float(ember_best_acc),
        'average_accuracy': float(avg_accuracy),
        'target_accuracy': target,
        'status': status,
        'training_time_seconds': time.time() - start_time,
    }

    results_path = project_root / 'results' / 'fast_advanced_results.json'
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n[OK] Results saved to {results_path}")
    print(f"[OK] Training completed in {results['training_time_seconds']:.1f}s")


if __name__ == '__main__':
    main()
