"""
Domain scanner module for DGA detection.
Handles domain feature extraction and malicious domain prediction.
"""

import pickle
from typing import Dict, Any, Tuple
from urllib.parse import urlparse
import tldextract
import math
from collections import Counter
import numpy as np

from ..config.config import (
    DOMAIN_MODEL_PATH, CONFIDENCE_THRESHOLD, MALWARE_THRESHOLD,
    DOMAIN_FEATURE_NAMES, Colors
)


class DomainScanner:
    """Handles domain scanning for DGA (Domain Generation Algorithm) detection"""
    
    def __init__(self, offline_mode: bool = False):
        """
        Initialize domain scanner.
        
        Args:
            offline_mode: If True, skip all API calls
        """
        self.offline_mode = offline_mode
        self.ml_model = None
        self._load_ml_model()
    
    def _load_ml_model(self):
        """Load the trained Random Forest model for domain classification"""
        try:
            if DOMAIN_MODEL_PATH.exists():
                with open(DOMAIN_MODEL_PATH, 'rb') as f:
                    self.ml_model = pickle.load(f)
                print(f"{Colors.OKGREEN}✓ Loaded Domain ML model{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ Domain ML model not found at {DOMAIN_MODEL_PATH}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error loading Domain ML model: {e}{Colors.ENDC}")
    
    @staticmethod
    def domain_entropy(domain: str) -> float:
        """
        Calculate Shannon entropy of a domain string.
        
        Args:
            domain: Domain string
        
        Returns:
            Entropy value
        """
        if not domain:
            return 0.0
        
        counts = Counter(domain)
        probs = [v / len(domain) for v in counts.values()]
        return -sum(p * math.log2(p) for p in probs)
    
    @staticmethod
    def vowel_ratio(domain: str) -> float:
        """
        Calculate ratio of vowels in domain.
        
        Args:
            domain: Domain string
        
        Returns:
            Vowel ratio (0-1)
        """
        if len(domain) == 0:
            return 0.0
        
        vowels = set('aeiou')
        return sum(1 for c in domain.lower() if c in vowels) / len(domain)
    
    @staticmethod
    def digit_ratio(domain: str) -> float:
        """
        Calculate ratio of digits in domain.
        
        Args:
            domain: Domain string
        
        Returns:
            Digit ratio (0-1)
        """
        if len(domain) == 0:
            return 0.0
        
        return sum(1 for c in domain if c.isdigit()) / len(domain)
    
    @staticmethod
    def consonant_ratio(domain: str) -> float:
        """
        Calculate ratio of consonants in domain.
        
        Args:
            domain: Domain string
        
        Returns:
            Consonant ratio (0-1)
        """
        if len(domain) == 0:
            return 0.0
        
        vowels = set('aeiou')
        return sum(1 for c in domain.lower() if c.isalpha() and c not in vowels) / len(domain)
    
    def extract_domain_features(self, domain: str) -> np.ndarray:
        """
        Extract features from a domain name.
        
        Args:
            domain: Domain name or URL
        
        Returns:
            Feature vector as numpy array
        """
        # Parse domain from URL if needed
        if domain.startswith('http://') or domain.startswith('https://'):
            parsed = urlparse(domain)
            domain = parsed.netloc or parsed.path
        
        # Extract main domain using tldextract
        extracted = tldextract.extract(domain)
        main_domain = extracted.domain.lower()
        
        if not main_domain:
            # If extraction failed, use the original domain
            main_domain = domain.lower().split('.')[0]
        
        # Calculate features
        features = {
            'length': len(main_domain),
            'entropy': self.domain_entropy(main_domain),
            'vowel_ratio': self.vowel_ratio(main_domain),
            'digit_ratio': self.digit_ratio(main_domain),
            'consonant_ratio': self.consonant_ratio(main_domain)
        }
        
        # Convert to numpy array in correct order
        feature_vector = np.array([features[name] for name in DOMAIN_FEATURE_NAMES], dtype=np.float32)
        
        return feature_vector.reshape(1, -1), features
    
    def predict_malicious(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict if domain is malicious using ML model.
        
        Args:
            features: Feature vector
        
        Returns:
            Tuple of (prediction, confidence)
        """
        if self.ml_model is None:
            return "UNKNOWN", 0.0
        
        try:
            # Get prediction probabilities
            proba = self.ml_model.predict_proba(features)[0]
            
            # Assuming class 1 is malicious, class 0 is benign
            malicious_prob = proba[1] if len(proba) > 1 else proba[0]
            
            # Determine prediction
            if malicious_prob >= MALWARE_THRESHOLD:
                prediction = "MALICIOUS"
            else:
                prediction = "BENIGN"
            
            return prediction, float(malicious_prob)
        
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error during prediction: {e}{Colors.ENDC}")
            return "UNKNOWN", 0.0
    
    def check_domain_reputation(self, domain: str) -> Dict[str, Any]:
        """
        Check domain reputation using external APIs (placeholder).
        Can be extended to use services like Google Safe Browsing, etc.
        
        Args:
            domain: Domain name
        
        Returns:
            Dictionary with reputation info
        """
        if self.offline_mode:
            return None
        
        # Placeholder for future API integrations
        # Could integrate: Google Safe Browsing, URLhaus, PhishTank, etc.
        return None
    
    def scan_domain(self, domain: str) -> Dict[str, Any]:
        """
        Perform complete domain scan including feature extraction and ML analysis.
        
        Args:
            domain: Domain name or URL to scan
        
        Returns:
            Dictionary containing complete scan results
        """
        print(f"\n{Colors.BOLD}Scanning domain: {domain}{Colors.ENDC}\n")
        
        results = {
            'domain': domain,
            'features': {},
            'ml_prediction': None,
            'ml_confidence': 0.0,
            'needs_quantum_analysis': False,
            'reputation': None
        }
        
        # Step 1: Extract features
        print(f"{Colors.OKCYAN}[1/3] Extracting domain features...{Colors.ENDC}")
        try:
            feature_vector, feature_dict = self.extract_domain_features(domain)
            results['features'] = feature_dict
            
            print(f"  Length: {feature_dict['length']}")
            print(f"  Entropy: {feature_dict['entropy']:.3f}")
            print(f"  Vowel ratio: {feature_dict['vowel_ratio']:.3f}")
            print(f"  Digit ratio: {feature_dict['digit_ratio']:.3f}")
            print(f"  Consonant ratio: {feature_dict['consonant_ratio']:.3f}\n")
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error extracting features: {e}{Colors.ENDC}")
            return results
        
        # Step 2: Check reputation (if available)
        print(f"{Colors.OKCYAN}[2/3] Checking domain reputation...{Colors.ENDC}")
        reputation = self.check_domain_reputation(domain)
        results['reputation'] = reputation
        
        if reputation:
            print(f"  Reputation data available")
        else:
            print(f"  {Colors.OKCYAN}ℹ No reputation data available{Colors.ENDC}")
        print()
        
        # Step 3: ML prediction
        print(f"{Colors.OKCYAN}[3/3] Running ML analysis...{Colors.ENDC}")
        prediction, confidence = self.predict_malicious(feature_vector)
        results['ml_prediction'] = prediction
        results['ml_confidence'] = confidence
        
        # Check if quantum analysis needed
        if confidence < CONFIDENCE_THRESHOLD:
            results['needs_quantum_analysis'] = True
            print(f"  {Colors.WARNING}⚠ Low confidence ({confidence:.2%}) - Quantum analysis recommended{Colors.ENDC}")
        else:
            print(f"  Prediction: {prediction} (confidence: {confidence:.2%})")
        
        return results
    
    def batch_scan_domains(self, domains: list) -> list:
        """
        Scan multiple domains in batch.
        
        Args:
            domains: List of domain names/URLs
        
        Returns:
            List of scan results
        """
        results = []
        
        print(f"\n{Colors.BOLD}Batch scanning {len(domains)} domains...{Colors.ENDC}")
        
        for i, domain in enumerate(domains, 1):
            print(f"\n{Colors.BOLD}[{i}/{len(domains)}]{Colors.ENDC}")
            result = self.scan_domain(domain)
            results.append(result)
        
        return results
