"""
Configuration module for Quantum-Enhanced Threat Scanner.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Model paths
MODELS_DIR = PROJECT_ROOT / "models"
DOMAIN_MODEL_PATH = MODELS_DIR / "domain_rf_model.pkl"
EMBER_MODEL_PATH = MODELS_DIR / "ember_rf_model.pkl"

# Quantum models
QUANTUM_MODELS_DIR = PROJECT_ROOT / "phase4" / "models"
QSVC_MODEL_PATH = QUANTUM_MODELS_DIR / "qsvc_domain_model.dill"
VQC_MODEL_PATH = QUANTUM_MODELS_DIR / "vqc_domain_model.dill"
QUANTUM_SCALER_PATH = QUANTUM_MODELS_DIR / "quantum_scaler.pkl"

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
DOMAIN_FEATURES_PATH = DATA_DIR / "domains" / "processed" / "domain_features.csv"
EMBER_FEATURES_PATH = DATA_DIR / "malware" / "processed" / "ember_features.csv"

# Logging
LOGS_DIR = PROJECT_ROOT / "scanner" / "logs"
SCAN_LOG_FILE = LOGS_DIR / "scan_history.json"
SCAN_CSV_LOG = LOGS_DIR / "scan_history.csv"

# API Configuration
VIRUSTOTAL_API_URL = "https://www.virustotal.com/api/v3/files/{hash}"
VIRUSTOTAL_SUBMIT_URL = "https://www.virustotal.com/api/v3/files"

# Thresholds
CONFIDENCE_THRESHOLD = 0.60  # Below this, trigger quantum analysis
MALWARE_THRESHOLD = 0.50     # Above this, classify as malware
HIGH_CONFIDENCE_THRESHOLD = 0.80  # High confidence detection

# Scanner settings
MAX_FILE_SIZE_MB = 100  # Maximum file size to scan (MB)
SUPPORTED_FILE_TYPES = ['.exe', '.dll', '.sys', '.scr']

# Colors for terminal output (ANSI codes)
class Colors:
    """Terminal color codes"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Feature names for EMBER model (based on EMBER dataset)
EMBER_FEATURE_NAMES = [
    'histogram_0', 'histogram_1', 'histogram_2', 'histogram_3', 'histogram_4',
    'histogram_5', 'histogram_6', 'histogram_7', 'histogram_8', 'histogram_9',
    'byteentropy_0', 'byteentropy_1', 'byteentropy_2', 'byteentropy_3', 'byteentropy_4',
    'byteentropy_5', 'byteentropy_6', 'byteentropy_7', 'byteentropy_8', 'byteentropy_9',
    'section_0', 'section_1', 'section_2', 'section_3', 'section_4',
    'imports_0', 'imports_1', 'imports_2', 'imports_3', 'imports_4',
    'exports_0', 'exports_1',
    'general_0', 'general_1', 'general_2', 'general_3', 'general_4'
]

# Domain feature names
DOMAIN_FEATURE_NAMES = ['length', 'entropy', 'vowel_ratio', 'digit_ratio', 'consonant_ratio']

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
