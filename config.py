"""
Centralized Configuration — Environment-based, no hardcoded secrets.

Loads settings from .env file and environment variables.
All modules should import from here instead of defining their own config.
"""

import os
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; environment variables still work

# ─────────────────────────────────────────────────────
# Project paths
# ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent

MODEL_DIR = PROJECT_ROOT / os.getenv('MODEL_DIR', 'models')
QUANTUM_MODEL_DIR = PROJECT_ROOT / os.getenv('QUANTUM_MODEL_DIR', 'phase4/models')
DATA_DIR = PROJECT_ROOT / 'data'
LOG_DIR = PROJECT_ROOT / os.getenv('LOG_DIR', 'logs')

# ─────────────────────────────────────────────────────
# Model paths
# ─────────────────────────────────────────────────────
DOMAIN_MODEL_PATH = MODEL_DIR / 'domain_rf_model.pkl'
EMBER_MODEL_PATH = MODEL_DIR / 'ember_rf_model.pkl'

QSVC_MODEL_PATH = QUANTUM_MODEL_DIR / 'qsvc_domain_model.dill'
VQC_MODEL_PATH = QUANTUM_MODEL_DIR / 'vqc_domain_model.dill'
QUANTUM_SCALER_PATH = QUANTUM_MODEL_DIR / 'quantum_scaler.pkl'

# ─────────────────────────────────────────────────────
# API keys — from environment only, NEVER from CLI args
# ─────────────────────────────────────────────────────
VT_API_KEY = os.getenv('VT_API_KEY')

# ─────────────────────────────────────────────────────
# API URLs
# ─────────────────────────────────────────────────────
VIRUSTOTAL_API_URL = 'https://www.virustotal.com/api/v3/files/{hash}'

# ─────────────────────────────────────────────────────
# Thresholds
# ─────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.60'))
MALWARE_THRESHOLD = float(os.getenv('MALWARE_THRESHOLD', '0.35'))
MAX_FILE_SIZE_MB = float(os.getenv('MAX_FILE_SIZE_MB', '100'))

# ─────────────────────────────────────────────────────
# Feature dimensions
# ─────────────────────────────────────────────────────
ML_FEATURE_DIM = 16
QUANTUM_FEATURE_DIM = 4

# ─────────────────────────────────────────────────────
# Supported file types for scanning
# ─────────────────────────────────────────────────────
SUPPORTED_FILE_TYPES = ['.exe', '.dll', '.sys', '.scr', '.bin']

# ─────────────────────────────────────────────────────
# Domain feature names (legacy 5 features for existing RF model)
# ─────────────────────────────────────────────────────
DOMAIN_FEATURE_NAMES = [
    'length', 'entropy', 'vowel_ratio', 'digit_ratio', 'consonant_ratio'
]

# ─────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / 'scanner.log', encoding='utf-8'),
    ]
)

# ─────────────────────────────────────────────────────
# Terminal colors (ANSI)
# ─────────────────────────────────────────────────────
class Colors:
    """Terminal color codes for CLI output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
