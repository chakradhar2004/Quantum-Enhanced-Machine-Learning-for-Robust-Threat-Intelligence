"""
Ensemble Voting Pipeline — Combines RF + QSVC + XGBoost

Provides weighted majority voting for higher accuracy
than any single model alone.
"""

import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class EnsembleVoter:
    """
    Weighted ensemble voting across multiple classifiers.

    Combines predictions from:
    - Classical ML (Random Forest, XGBoost)
    - Quantum ML (QSVC)

    The final prediction uses weighted average of probabilities
    where weights are proportional to each model's validation accuracy.
    """

    def __init__(self):
        self.models: Dict[str, dict] = {}

    def add_model(self, name: str, model: Any, weight: float = 1.0,
                  preprocessor: Any = None):
        """
        Register a model for the ensemble.

        Args:
            name: Unique model identifier
            model: Trained model with predict/predict_proba
            weight: Voting weight (higher = more influence)
            preprocessor: Optional preprocessing pipeline (scaler, PCA, etc.)
        """
        self.models[name] = {
            'model': model,
            'weight': weight,
            'preprocessor': preprocessor,
        }
        logger.info(f"Added model '{name}' (weight={weight:.2f})")

    def predict(self, features: np.ndarray) -> Tuple[str, float, Dict[str, Any]]:
        """
        Make ensemble prediction.

        Args:
            features: Input feature vector

        Returns:
            (prediction, confidence, details_per_model)
        """
        if not self.models:
            return 'UNKNOWN', 0.0, {}

        if features.ndim == 1:
            features = features.reshape(1, -1)

        weighted_probs = []
        total_weight = 0.0
        details = {}

        for name, info in self.models.items():
            model = info['model']
            weight = info['weight']
            preprocessor = info['preprocessor']

            try:
                # Apply preprocessor if available
                x = features.copy()
                if preprocessor is not None:
                    x = preprocessor.transform(x)

                # Get probability
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(x)[0]
                    mal_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
                elif hasattr(model, 'decision_function'):
                    dec = model.decision_function(x)[0]
                    mal_prob = float(1.0 / (1.0 + np.exp(-dec)))  # sigmoid
                else:
                    pred = model.predict(x)[0]
                    mal_prob = 1.0 if pred == 1 else 0.0

                weighted_probs.append(mal_prob * weight)
                total_weight += weight

                details[name] = {
                    'prediction': 'MALICIOUS' if mal_prob >= 0.5 else 'BENIGN',
                    'probability': mal_prob,
                    'weight': weight,
                }

            except Exception as e:
                logger.warning(f"Model '{name}' failed: {e}")
                details[name] = {'error': str(e)}

        if total_weight == 0:
            return 'UNKNOWN', 0.0, details

        # Weighted average probability
        ensemble_prob = sum(weighted_probs) / total_weight
        prediction = 'MALICIOUS' if ensemble_prob >= 0.5 else 'BENIGN'

        # Confidence = distance from decision boundary
        confidence = abs(ensemble_prob - 0.5) * 2  # Scale to 0-1

        details['_ensemble'] = {
            'prediction': prediction,
            'probability': float(ensemble_prob),
            'confidence': float(confidence),
            'n_models_voted': len(weighted_probs),
            'total_weight': float(total_weight),
        }

        return prediction, float(ensemble_prob), details


def create_default_ensemble(
    rf_model=None,
    qsvc_model=None,
    xgb_model=None,
    qsvc_preprocessor=None,
    rf_weight: float = 0.4,
    qsvc_weight: float = 0.35,
    xgb_weight: float = 0.25,
) -> EnsembleVoter:
    """
    Create a default ensemble with standard weights.

    Args:
        rf_model: Trained Random Forest model
        qsvc_model: Trained QSVC model
        xgb_model: Trained XGBoost model
        qsvc_preprocessor: Scaler/PCA for QSVC features
        rf_weight: Weight for RF (default 0.4)
        qsvc_weight: Weight for QSVC (default 0.35)
        xgb_weight: Weight for XGBoost (default 0.25)

    Returns:
        Configured EnsembleVoter
    """
    ensemble = EnsembleVoter()

    if rf_model is not None:
        ensemble.add_model('random_forest', rf_model, weight=rf_weight)

    if qsvc_model is not None:
        ensemble.add_model(
            'qsvc', qsvc_model, weight=qsvc_weight,
            preprocessor=qsvc_preprocessor,
        )

    if xgb_model is not None:
        ensemble.add_model('xgboost', xgb_model, weight=xgb_weight)

    return ensemble
