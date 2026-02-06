"""
Simplified configuration for threat scanner
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = PROJECT_ROOT / 'phase3' / 'models'

# Model paths
EMBER_MODEL = MODELS_DIR / 'rf_model.pkl'
DOMAIN_MODEL = MODELS_DIR / 'domain_model.pkl'
QSVC_MODEL = MODELS_DIR / 'qsvc_metadata.json'
VQC_MODEL = MODELS_DIR / 'vqc_metadata.json'

# Data paths
EMBER_DATA = DATA_DIR / 'ember2018'
DOMAIN_DATA = DATA_DIR / 'domains'
SAMPLE_DATA = DATA_DIR / 'samples'

# Analysis settings
MAX_FILE_SIZE_MB = 100
MIN_CONFIDENCE = 0.5
ANOMALY_THRESHOLD = 0.7

# Feature dimensions
ML_FEATURE_DIM = 16
QUANTUM_FEATURE_DIM = 4
