"""
Model utilities for loading and using trained models.
"""

import pickle
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

try:
    import dill
    DILL_AVAILABLE = True
except ImportError:
    DILL_AVAILABLE = False


class ModelLoader:
    """Load and manage trained models"""
    
    def __init__(self, models_dir: Path):
        """
        Initialize model loader.
        
        Args:
            models_dir: Directory containing model files
        """
        self.models_dir = Path(models_dir)
        self.models = {}
    
    def load_pickle_model(self, model_path: Path, name: str):
        """Load a pickle model"""
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            self.models[name] = model
            print(f"✓ Loaded {name} from {model_path.name}")
            return model
        except Exception as e:
            print(f"✗ Error loading {name}: {e}")
            return None
    
    def load_dill_model(self, model_path: Path, name: str):
        """Load a dill model (for quantum models)"""
        if not DILL_AVAILABLE:
            print("✗ Dill not available. Install with: pip install dill")
            return None
        
        try:
            with open(model_path, 'rb') as f:
                model = dill.load(f)
            self.models[name] = model
            print(f"✓ Loaded {name} from {model_path.name}")
            return model
        except Exception as e:
            print(f"✗ Error loading {name}: {e}")
            return None
    
    def get_model(self, name: str):
        """Get a loaded model by name"""
        return self.models.get(name)
    
    def predict(self, model_name: str, features: np.ndarray) -> Tuple[Optional[int], Optional[float]]:
        """
        Make prediction using a model.
        
        Args:
            model_name: Name of the model to use
            features: Feature vector
        
        Returns:
            Tuple of (prediction, confidence)
        """
        model = self.get_model(model_name)
        if model is None:
            return None, None
        
        try:
            # Get prediction
            pred = model.predict(features)[0]
            
            # Try to get probability
            try:
                proba = model.predict_proba(features)[0]
                confidence = float(max(proba))
            except:
                confidence = 0.5
            
            return int(pred), confidence
        
        except Exception as e:
            print(f"✗ Prediction error: {e}")
            return None, None


def load_all_models(project_root: Path) -> ModelLoader:
    """
    Load all trained models from the project.
    
    Args:
        project_root: Root directory of the project
    
    Returns:
        ModelLoader instance with all models loaded
    """
    loader = ModelLoader(project_root / 'models')
    
    # Load classical ML models
    domain_model = project_root / 'models' / 'domain_rf_model.pkl'
    if domain_model.exists():
        loader.load_pickle_model(domain_model, 'domain_rf')
    
    ember_model = project_root / 'models' / 'ember_rf_model.pkl'
    if ember_model.exists():
        loader.load_pickle_model(ember_model, 'ember_rf')
    
    # Load quantum models
    qsvc_model = project_root / 'phase4' / 'models' / 'qsvc_domain_model.dill'
    if qsvc_model.exists():
        loader.load_dill_model(qsvc_model, 'qsvc')
    
    vqc_model = project_root / 'phase4' / 'models' / 'vqc_domain_model.dill'
    if vqc_model.exists():
        loader.load_dill_model(vqc_model, 'vqc')
    
    # Load scaler
    scaler_path = project_root / 'phase4' / 'models' / 'quantum_scaler.pkl'
    if scaler_path.exists():
        loader.load_pickle_model(scaler_path, 'scaler')
    
    return loader
