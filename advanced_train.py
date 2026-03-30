#!/usr/bin/env python3
"""
Advanced Multi-Model Training Pipeline
Trains multiple algorithms with hyperparameter tuning and ensemble voting.
Uses entire datasets (not limited to 500 samples).
"""

import numpy as np
import pandas as pd
import pickle
import json
import time
import warnings
from pathlib import Path
from typing import Dict, Tuple, Any
from collections import defaultdict

warnings.filterwarnings('ignore')

from sklearn.model_selection import (
    train_test_split, GridSearchCV, RandomizedSearchCV,
    StratifiedKFold, cross_val_score
)
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier,
    ExtraTreesClassifier, VotingClassifier, StackingClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False

try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False

project_root = Path(__file__).parent


class AdvancedModelTrainer:
    """Multi-algorithm trainer with hyperparameter optimization."""

    def __init__(self, name: str):
        self.name = name
        self.models = {}
        self.results = {}
        self.best_model = None
        self.scaler = StandardScaler()

    def load_domain_data(self, sample_fraction=1.0):
        """Load full domain dataset or fraction."""
        path = project_root / 'data' / 'domains' / 'processed' / 'domain_features.csv'
        df = pd.read_csv(path)

        if sample_fraction < 1.0:
            df = df.sample(frac=sample_fraction, random_state=42)

        X = df.drop('label', axis=1).values
        y = df['label'].values

        return X, y, df.columns[:-1].tolist()

    def load_ember_data(self, sample_fraction=1.0):
        """Load full EMBER dataset or fraction."""
        path = project_root / 'data' / 'malware' / 'processed' / 'ember_features.csv'
        df = pd.read_csv(path)

        if sample_fraction < 1.0:
            df = df.sample(frac=sample_fraction, random_state=42)

        # One-hot encode machine type
        machine_dummies = pd.get_dummies(df['machine'], prefix='machine')
        df = df.drop(columns='machine')
        df = pd.concat([df, machine_dummies], axis=1)

        X = df.drop('label', axis=1).values
        y = df['label'].values
        feature_names = df.drop('label', axis=1).columns.tolist()

        return X, y, feature_names

    def apply_smote(self, X_train, y_train):
        """Apply SMOTE for class balance."""
        if not SMOTE_AVAILABLE:
            return X_train, y_train

        class_dist = dict(zip(*np.unique(y_train, return_counts=True)))
        if len(class_dist) < 2 or min(class_dist.values()) > 1000:
            return X_train, y_train

        smote = SMOTE(random_state=42, k_neighbors=5)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f"[OK] Applied SMOTE - new distribution: {dict(zip(*np.unique(y_train, return_counts=True)))}")

        return X_train, y_train

    def train_random_forest(self, X_train, X_test, y_train, y_test, cv=None):
        """Train optimized Random Forest."""
        print("\n--- Random Forest ---")

        param_grid = {
            'n_estimators': [300, 400],
            'max_depth': [25, 30],
            'min_samples_split': [5],
            'min_samples_leaf': [2],
            'max_features': ['sqrt'],
        }

        rf = RandomForestClassifier(class_weight='balanced', random_state=42, n_jobs=-1)

        grid = GridSearchCV(rf, param_grid, cv=5, n_jobs=-1, verbose=0)
        grid.fit(X_train, y_train)

        best_rf = grid.best_estimator_
        print(f"[OK] Best params: {grid.best_params_}")

        y_pred = best_rf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, best_rf.predict_proba(X_test)[:, 1])

        print(f"Accuracy: {acc:.4f}, AUC: {auc:.4f}")

        return best_rf, acc, auc

    def train_gradient_boosting(self, X_train, X_test, y_train, y_test):
        """Train Gradient Boosting."""
        print("\n--- Gradient Boosting ---")

        gb = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=7,
            min_samples_split=5,
            subsample=0.9,
            random_state=42
        )

        gb.fit(X_train, y_train)
        y_pred = gb.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, gb.predict_proba(X_test)[:, 1])

        print(f"Accuracy: {acc:.4f}, AUC: {auc:.4f}")

        return gb, acc, auc

    def train_extra_trees(self, X_train, X_test, y_train, y_test):
        """Train Extra Trees."""
        print("\n--- Extra Trees ---")

        et = ExtraTreesClassifier(
            n_estimators=400,
            max_depth=30,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )

        et.fit(X_train, y_train)
        y_pred = et.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, et.predict_proba(X_test)[:, 1])

        print(f"Accuracy: {acc:.4f}, AUC: {auc:.4f}")

        return et, acc, auc

    def train_xgboost(self, X_train, X_test, y_train, y_test):
        """Train XGBoost."""
        if not XGB_AVAILABLE:
            print("[SKIP] XGBoost not available")
            return None, 0, 0

        print("\n--- XGBoost ---")

        xgb_model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            scale_pos_weight=sum(y_train == 0) / sum(y_train == 1),
            random_state=42,
            n_jobs=-1,
        )

        xgb_model.fit(X_train, y_train)
        y_pred = xgb_model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, xgb_model.predict_proba(X_test)[:, 1])

        print(f"Accuracy: {acc:.4f}, AUC: {auc:.4f}")

        return xgb_model, acc, auc

    def train_lightgbm(self, X_train, X_test, y_train, y_test):
        """Train LightGBM."""
        if not LGB_AVAILABLE:
            print("[SKIP] LightGBM not available")
            return None, 0, 0

        print("\n--- LightGBM ---")

        lgb_model = lgb.LGBMClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.1,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
        )

        lgb_model.fit(X_train, y_train)
        y_pred = lgb_model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, lgb_model.predict_proba(X_test)[:, 1])

        print(f"Accuracy: {acc:.4f}, AUC: {auc:.4f}")

        return lgb_model, acc, auc

    def create_voting_ensemble(self, models_dict):
        """Create weighted voting classifier."""
        print("\n--- Weighted Voting Ensemble ---")

        estimators = [
            ('rf', models_dict.get('rf')),
            ('gb', models_dict.get('gb')),
            ('et', models_dict.get('et')),
        ]
        estimators = [(n, m) for n, m in estimators if m is not None]

        if len(estimators) < 2:
            print("[SKIP] Not enough models for ensemble")
            return None

        voting_clf = VotingClassifier(
            estimators=estimators,
            voting='soft',
            weights=[0.35, 0.35, 0.30]
        )

        return voting_clf

    def train_dataset(self, X, y, data_type='domain'):
        """Train all models on dataset."""
        print(f"\n{'='*70}")
        print(f"ADVANCED TRAINING: {self.name.upper()}")
        print(f"{'='*70}")

        print(f"\nDataset: {len(X)} samples, {X.shape[1]} features")
        print(f"Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"Train: {len(X_train)}, Test: {len(X_test)}")

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Apply SMOTE
        if SMOTE_AVAILABLE:
            X_train_scaled, y_train = self.apply_smote(X_train_scaled, y_train)

        # Train models
        models_dict = {}

        rf_model, rf_acc, rf_auc = self.train_random_forest(X_train_scaled, X_test_scaled, y_train, y_test)
        models_dict['rf'] = rf_model
        self.results['rf'] = {'accuracy': rf_acc, 'auc': rf_auc}

        gb_model, gb_acc, gb_auc = self.train_gradient_boosting(X_train_scaled, X_test_scaled, y_train, y_test)
        models_dict['gb'] = gb_model
        self.results['gb'] = {'accuracy': gb_acc, 'auc': gb_auc}

        et_model, et_acc, et_auc = self.train_extra_trees(X_train_scaled, X_test_scaled, y_train, y_test)
        models_dict['et'] = et_model
        self.results['et'] = {'accuracy': et_acc, 'auc': et_auc}

        xgb_model, xgb_acc, xgb_auc = self.train_xgboost(X_train_scaled, X_test_scaled, y_train, y_test)
        if xgb_model:
            models_dict['xgb'] = xgb_model
            self.results['xgb'] = {'accuracy': xgb_acc, 'auc': xgb_auc}

        lgb_model, lgb_acc, lgb_auc = self.train_lightgbm(X_train_scaled, X_test_scaled, y_train, y_test)
        if lgb_model:
            models_dict['lgb'] = lgb_model
            self.results['lgb'] = {'accuracy': lgb_acc, 'auc': lgb_auc}

        # Create ensemble
        ensemble = self.create_voting_ensemble(models_dict)
        if ensemble:
            ensemble.fit(X_train_scaled, y_train)
            y_pred_ens = ensemble.predict(X_test_scaled)
            ens_acc = accuracy_score(y_test, y_pred_ens)
            ens_auc = roc_auc_score(y_test, ensemble.predict_proba(X_test_scaled)[:, 1])
            print(f"Ensemble Accuracy: {ens_acc:.4f}, AUC: {ens_auc:.4f}")
            models_dict['ensemble'] = ensemble
            self.results['ensemble'] = {'accuracy': ens_acc, 'auc': ens_auc}

        # Select best model
        best_name = max(self.results, key=lambda x: self.results[x]['accuracy'])
        self.best_model = models_dict[best_name]
        best_acc = self.results[best_name]['accuracy']

        print(f"\n{'='*70}")
        print(f"BEST MODEL: {best_name.upper()}")
        print(f"Accuracy: {best_acc:.4f} ({best_acc*100:.1f}%)")
        print(f"{'='*70}")

        # Summary table
        print("\nAll Models Summary:")
        print(f"{'Model':<15} {'Accuracy':<12} {'AUC':<12}")
        print("-" * 40)
        for model_name, metrics in sorted(self.results.items(),
                                         key=lambda x: x[1]['accuracy'], reverse=True):
            print(f"{model_name:<15} {metrics['accuracy']:.4f}      {metrics['auc']:.4f}")

        return models_dict, self.results


def main():
    print("="*70)
    print("ADVANCED MULTI-MODEL TRAINING PIPELINE")
    print("="*70)

    all_results = {}

    # Train domain models
    domain_trainer = AdvancedModelTrainer("Domain Classification")
    X_domain, y_domain, _ = domain_trainer.load_domain_data(sample_fraction=1.0)  # Full dataset
    domain_models, domain_results = domain_trainer.train_dataset(X_domain, y_domain, 'domain')

    # Save best domain model
    best_domain = domain_trainer.best_model
    domain_path = project_root / 'models' / 'domain_best_model.pkl'
    with open(domain_path, 'wb') as f:
        pickle.dump(best_domain, f)
    print(f"\n[OK] Best domain model saved to {domain_path}")

    all_results['domain'] = domain_results

    # Train EMBER models
    print("\n" + "="*70)
    ember_trainer = AdvancedModelTrainer("EMBER Classification")
    X_ember, y_ember, _ = ember_trainer.load_ember_data(sample_fraction=1.0)  # Full dataset
    ember_models, ember_results = ember_trainer.train_dataset(X_ember, y_ember, 'ember')

    # Save best EMBER model
    best_ember = ember_trainer.best_model
    ember_path = project_root / 'models' / 'ember_best_model.pkl'
    with open(ember_path, 'wb') as f:
        pickle.dump(best_ember, f)
    print(f"\n[OK] Best EMBER model saved to {ember_path}")

    all_results['ember'] = ember_results

    # Calculate ensemble accuracy
    domain_best_acc = max(domain_results.values(), key=lambda x: x['accuracy'])['accuracy']
    ember_best_acc = max(ember_results.values(), key=lambda x: x['accuracy'])['accuracy']
    ensemble_accuracy = (domain_best_acc + ember_best_acc) / 2

    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"Domain Best Accuracy: {domain_best_acc:.4f} ({domain_best_acc*100:.1f}%)")
    print(f"EMBER Best Accuracy:  {ember_best_acc:.4f} ({ember_best_acc*100:.1f}%)")
    print(f"Average Accuracy:     {ensemble_accuracy:.4f} ({ensemble_accuracy*100:.1f}%)")

    target = 0.85
    if ensemble_accuracy >= target:
        print(f"\n[SUCCESS] TARGET ACHIEVED: {ensemble_accuracy*100:.1f}% >= {target*100:.1f}%")
    else:
        gap = target - ensemble_accuracy
        print(f"\n[INFO] Gap to target: {gap*100:.1f}%")

    # Save detailed results
    results_path = project_root / 'results' / 'advanced_training_results.json'
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump({
            'domain_results': domain_results,
            'ember_results': ember_results,
            'domain_best_accuracy': domain_best_acc,
            'ember_best_accuracy': ember_best_acc,
            'average_accuracy': ensemble_accuracy,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        }, f, indent=2)

    print(f"\n[OK] Results saved to {results_path}")


if __name__ == '__main__':
    main()
