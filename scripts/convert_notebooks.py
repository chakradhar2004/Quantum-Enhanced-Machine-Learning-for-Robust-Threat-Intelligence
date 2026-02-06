"""
Utility script to convert notebook code into reusable modules.
This extracts key functions from Jupyter notebooks for production use.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_feature_extraction_module():
    """Create standalone feature extraction module from notebooks"""
    
    code = '''"""
Feature extraction utilities for threat intelligence.
Extracted from Jupyter notebooks for production use.
"""

import pandas as pd
import numpy as np
import tldextract
import string
import math
from collections import Counter
from typing import Dict, Any, List
import json


class DomainFeatureExtractor:
    """Extract features from domain names"""
    
    @staticmethod
    def domain_entropy(domain: str) -> float:
        """Calculate Shannon entropy of a domain"""
        if not domain:
            return 0.0
        counts = Counter(domain)
        probs = [v / len(domain) for v in counts.values()]
        return -sum(p * math.log2(p) for p in probs)
    
    @staticmethod
    def vowel_ratio(domain: str) -> float:
        """Calculate vowel ratio"""
        if len(domain) == 0:
            return 0.0
        vowels = set('aeiou')
        return sum(1 for c in domain.lower() if c in vowels) / len(domain)
    
    @staticmethod
    def digit_ratio(domain: str) -> float:
        """Calculate digit ratio"""
        if len(domain) == 0:
            return 0.0
        return sum(1 for c in domain if c.isdigit()) / len(domain)
    
    @staticmethod
    def consonant_ratio(domain: str) -> float:
        """Calculate consonant ratio"""
        if len(domain) == 0:
            return 0.0
        vowels = set('aeiou')
        return sum(1 for c in domain.lower() if c.isalpha() and c not in vowels) / len(domain)
    
    def extract_features(self, domain: str) -> Dict[str, float]:
        """
        Extract all features from a domain.
        
        Args:
            domain: Domain name or URL
        
        Returns:
            Dictionary of features
        """
        # Parse domain
        extracted = tldextract.extract(domain)
        main_domain = extracted.domain.lower()
        
        if not main_domain:
            main_domain = domain.lower().split('.')[0]
        
        return {
            'length': len(main_domain),
            'entropy': self.domain_entropy(main_domain),
            'vowel_ratio': self.vowel_ratio(main_domain),
            'digit_ratio': self.digit_ratio(main_domain),
            'consonant_ratio': self.consonant_ratio(main_domain)
        }
    
    def extract_batch(self, domains: List[str]) -> pd.DataFrame:
        """Extract features from multiple domains"""
        features = [self.extract_features(d) for d in domains]
        return pd.DataFrame(features)


class MalwareFeatureExtractor:
    """Extract features from malware samples (EMBER format)"""
    
    @staticmethod
    def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
        """Load JSONL file"""
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    
    @staticmethod
    def extract_ember_features(sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from EMBER format sample.
        
        Args:
            sample: EMBER format dictionary
        
        Returns:
            Flattened feature dictionary
        """
        features = {}
        
        # Histogram features
        if 'histogram' in sample:
            hist = sample['histogram']
            for i, val in enumerate(hist[:10]):  # Take first 10
                features[f'histogram_{i}'] = val
        
        # Byte entropy features
        if 'byteentropy' in sample:
            ent = sample['byteentropy']
            for i, val in enumerate(ent[:10]):
                features[f'byteentropy_{i}'] = val
        
        # Section features
        if 'section' in sample:
            sec = sample['section']
            for i in range(5):
                features[f'section_{i}'] = sec.get(f'section_{i}', 0)
        
        # Import features
        if 'imports' in sample:
            imp = sample['imports']
            for i in range(5):
                features[f'imports_{i}'] = imp.get(f'imports_{i}', 0)
        
        # Export features
        if 'exports' in sample:
            exp = sample['exports']
            for i in range(2):
                features[f'exports_{i}'] = exp.get(f'exports_{i}', 0)
        
        # General features
        if 'general' in sample:
            gen = sample['general']
            for i in range(5):
                features[f'general_{i}'] = gen.get(f'general_{i}', 0)
        
        # Label
        features['label'] = sample.get('label', -1)
        
        return features
    
    def process_ember_dataset(self, data_dir: Path, output_path: Path):
        """Process EMBER dataset from raw JSONL to CSV"""
        all_features = []
        
        # Process all JSONL files
        for jsonl_file in data_dir.glob('*.jsonl'):
            print(f"Processing {jsonl_file.name}...")
            samples = self.load_jsonl(jsonl_file)
            
            for sample in samples:
                try:
                    features = self.extract_ember_features(sample)
                    all_features.append(features)
                except Exception as e:
                    print(f"Error processing sample: {e}")
                    continue
        
        # Convert to DataFrame
        df = pd.DataFrame(all_features)
        
        # Save
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} samples to {output_path}")
        
        return df


# Convenience functions
def extract_domain_features(domain: str) -> Dict[str, float]:
    """Quick function to extract domain features"""
    extractor = DomainFeatureExtractor()
    return extractor.extract_features(domain)


def extract_malware_features(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Quick function to extract malware features"""
    extractor = MalwareFeatureExtractor()
    return extractor.extract_ember_features(sample)
'''
    
    # Write to file
    output_path = Path(__file__).parent.parent / 'scanner' / 'utils' / 'feature_extraction.py'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"Created {output_path}")


def create_model_utils():
    """Create model loading and inference utilities"""
    
    code = '''"""
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
'''
    
    output_path = Path(__file__).parent.parent / 'scanner' / 'utils' / 'model_utils.py'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"Created {output_path}")


def create_utils_init():
    """Create utils __init__.py"""
    code = '''"""Utility modules for the scanner"""
from .feature_extraction import DomainFeatureExtractor, MalwareFeatureExtractor
from .model_utils import ModelLoader, load_all_models

__all__ = [
    'DomainFeatureExtractor',
    'MalwareFeatureExtractor',
    'ModelLoader',
    'load_all_models'
]
'''
    
    output_path = Path(__file__).parent.parent / 'scanner' / 'utils' / '__init__.py'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"Created {output_path}")


def main():
    """Main function"""
    print("Converting Jupyter notebooks to production modules...\n")
    
    create_feature_extraction_module()
    create_model_utils()
    create_utils_init()
    
    print("\n✓ Conversion complete!")
    print("\nGenerated modules:")
    print("  - scanner/utils/feature_extraction.py")
    print("  - scanner/utils/model_utils.py")
    print("  - scanner/utils/__init__.py")


if __name__ == '__main__':
    main()
