"""
File scanner module for malware detection.
Handles file hashing, VirusTotal API integration, and strict PE feature extraction.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests
import pickle
import numpy as np

# Injecting path to import utils
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.features import FileFeatureExtractor

from ..config.config import (
    EMBER_MODEL_PATH, VIRUSTOTAL_API_URL, MAX_FILE_SIZE_MB,
    MALWARE_THRESHOLD, CONFIDENCE_THRESHOLD,
    Colors
)

class FileScanner:
    """Handles file scanning for malware detection"""
    
    def __init__(self, vt_api_key: Optional[str] = None, offline_mode: bool = False):
        self.vt_api_key = vt_api_key
        self.offline_mode = offline_mode
        self.ml_model = None
        self.feature_extractor = FileFeatureExtractor()
        self._load_ml_model()
    
    def _load_ml_model(self):
        """Load the trained Random Forest model for malware detection"""
        try:
            if EMBER_MODEL_PATH.exists():
                with open(EMBER_MODEL_PATH, 'rb') as f:
                    self.ml_model = pickle.load(f)
                print(f"{Colors.OKGREEN}✓ Loaded EMBER ML model{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ ML model not found at {EMBER_MODEL_PATH}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error loading ML model: {e}{Colors.ENDC}")
    
    def hash_file(self, file_path: Path) -> Dict[str, str]:
        md5_hash = hashlib.md5()
        sha1_hash = hashlib.sha1()
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
                    sha1_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            return {
                'md5': md5_hash.hexdigest(),
                'sha1': sha1_hash.hexdigest(),
                'sha256': sha256_hash.hexdigest()
            }
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error hashing file: {e}{Colors.ENDC}")
            return {}
    
    def check_virustotal(self, file_hash: str) -> Optional[Dict[str, Any]]:
        if self.offline_mode or not self.vt_api_key:
            return None
        try:
            url = VIRUSTOTAL_API_URL.format(hash=file_hash)
            response = requests.get(url, headers={'x-apikey': self.vt_api_key}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'total_engines': sum(stats.values()),
                }
        except Exception:
            return None
        return None
    
    def extract_pe_features(self, file_path: Path) -> Optional[np.ndarray]:
        """Strict extraction algorithm that prohibits generic feature generation."""
        try:
            features = self.feature_extractor.extract(file_path)
            
            if features is None:
                print(f"{Colors.WARNING}⚠ Cannot extract PE features. Invalid or missing PE headers.{Colors.ENDC}")
                return None
            
            # Ensure features match length (16 expected from Ember model implementation)
            if features.shape[1] != 16:
                print(f"{Colors.WARNING}⚠ Feature length mismatch. Got {features.shape[1]}.{Colors.ENDC}")
                return None
            
            if np.isnan(features).any():
                print(f"{Colors.WARNING}⚠ Features contain NaN values.{Colors.ENDC}")
                return None
            
            # Debugging Output
            print("Features:", features.tolist())
            return features
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Exception parsing PE features: {e}. Returning UNKNOWN.{Colors.ENDC}")
            return None
    
    def predict_malware(self, features: np.ndarray) -> Tuple[str, float]:
        if self.ml_model is None or features is None:
            return "UNKNOWN", 0.0
        
        try:
            prob = self.ml_model.predict_proba(features)[0][1]
            print("ML probability:", float(prob))
            
            # Use config thresholds — consistent with cli.py
            if prob >= MALWARE_THRESHOLD:       # 0.50 → MALICIOUS
                verdict = "MALICIOUS"
            elif prob >= MALWARE_THRESHOLD - 0.1:  # 0.40-0.49 → SUSPICIOUS
                verdict = "SUSPICIOUS"
            else:
                verdict = "BENIGN"
                
            return verdict, float(prob)
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error during prediction: {e}{Colors.ENDC}")
            return "UNKNOWN", 0.0
            
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Unified response output requested by prompt.
        { verdict, confidence, model_used, features_valid }
        Additional legacy keys appended to maintain ThreatScanner/Streamlit compat.
        """
        file_path = Path(file_path)
        
        if not file_path.exists() or not file_path.is_file():
            return {
                "verdict": "UNKNOWN", "confidence": 0.0, "model_used": "NONE",
                "features_valid": False, 'error': 'Invalid file',
                'ml_prediction': 'UNKNOWN', 'ml_confidence': 0.0
            }
            
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB or file_size_mb == 0:
            return {
                "verdict": "UNKNOWN", "confidence": 0.0, "model_used": "NONE",
                "features_valid": False, 'error': f'Invalid file size {file_size_mb} MB',
                'ml_prediction': 'UNKNOWN', 'ml_confidence': 0.0
            }
            
        features = self.extract_pe_features(file_path)
        if features is None:
            return {
                "verdict": "UNKNOWN", "confidence": 0.0, "model_used": "NONE",
                "features_valid": False, "hashes": self.hash_file(file_path),
                'ml_prediction': 'UNKNOWN', 'ml_confidence': 0.0,
                'needs_quantum_analysis': False
            }
            
        verdict, confidence = self.predict_malware(features)
        
        # Only invoke quantum if confidence is near the decision boundary
        needs_quantum = abs(confidence - MALWARE_THRESHOLD) < (1.0 - CONFIDENCE_THRESHOLD)
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "model_used": "RF",
            "features_valid": True,
            "hashes": self.hash_file(file_path),
            "file_size_mb": file_size_mb,
            "needs_quantum_analysis": needs_quantum,
            # Legacy mapping for ThreatScanner framework overrides
            "ml_prediction": verdict,
            "ml_confidence": confidence
        }
