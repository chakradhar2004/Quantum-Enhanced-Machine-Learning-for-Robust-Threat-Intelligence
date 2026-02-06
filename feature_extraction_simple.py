"""
Simple feature extraction for threat detection
"""

import math
import numpy as np
from collections import Counter
from typing import Dict, List, Optional


class FeatureExtractor:
    """Extract features from files and domains"""
    
    @staticmethod
    def file_entropy(data: bytes) -> float:
        """Calculate Shannon entropy of file"""
        if not data:
            return 0.0
        
        counts = Counter(data)
        entropy = 0.0
        data_len = len(data)
        
        for count in counts.values():
            p = count / data_len
            entropy -= p * math.log2(p)
        
        return entropy
    
    @staticmethod
    def byte_histogram(data: bytes, bins: int = 8) -> List[float]:
        """Byte value distribution"""
        if not data:
            return [0.0] * bins
        
        hist = [0] * 256
        for byte in data:
            hist[byte] += 1
        
        # Aggregate into bins
        bytes_per_bin = 256 // bins
        result = []
        for i in range(bins):
            start = i * bytes_per_bin
            end = (i + 1) * bytes_per_bin
            count = sum(hist[start:end])
            result.append(count / len(data))
        
        return result
    
    @staticmethod
    def extract_file_features(data: bytes) -> Dict[str, float]:
        """Basic file features"""
        features = {}
        
        # Size
        features['size'] = len(data)
        features['size_kb'] = len(data) / 1024
        
        # Entropy
        features['entropy'] = FeatureExtractor.file_entropy(data)
        
        # Byte statistics
        features['null_ratio'] = data.count(b'\x00') / len(data) if data else 0
        features['high_bytes_ratio'] = sum(1 for b in data if b >= 128) / len(data) if data else 0
        features['low_bytes_ratio'] = sum(1 for b in data if b < 32) / len(data) if data else 0
        
        # Printable ASCII ratio
        printable = sum(1 for b in data if 32 <= b <= 126)
        features['ascii_ratio'] = printable / len(data) if data else 0
        
        # PE detection
        features['is_pe'] = 1.0 if data[:2] == b'MZ' else 0.0
        features['is_elf'] = 1.0 if data[:4] == b'\x7fELF' else 0.0
        
        # Common malware patterns
        features['has_nops'] = 1.0 if b'\x90\x90\x90' in data else 0.0
        
        return features
    
    @staticmethod
    def extract_domain_features(domain: str) -> Dict[str, float]:
        """Domain-based features"""
        domain = domain.lower().split('/')[0]
        features = {}
        
        # Basic properties
        features['length'] = len(domain)
        features['subdomain_count'] = domain.count('.')
        
        # Character analysis
        features['entropy'] = FeatureExtractor._text_entropy(domain)
        features['digit_ratio'] = sum(1 for c in domain if c.isdigit()) / len(domain) if domain else 0
        features['vowel_ratio'] = sum(1 for c in domain if c in 'aeiou') / len(domain) if domain else 0
        features['consonant_ratio'] = sum(1 for c in domain if c.isalpha() and c not in 'aeiou') / len(domain) if domain else 0
        
        # Suspicious patterns
        features['has_numbers'] = 1.0 if any(c.isdigit() for c in domain) else 0.0
        features['has_hyphen'] = 1.0 if '-' in domain else 0.0
        
        return features
    
    @staticmethod
    def _text_entropy(text: str) -> float:
        """Shannon entropy for text"""
        if not text:
            return 0.0
        
        counts = Counter(text)
        entropy = 0.0
        
        for count in counts.values():
            p = count / len(text)
            entropy -= p * math.log2(p)
        
        return entropy


class ScanLogger:
    """Simple logging for scans"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.memory_log = []
    
    def log_scan(self, scan_data: Dict) -> None:
        """Log scan results"""
        self.memory_log.append(scan_data)
        
        if self.log_file:
            with open(self.log_file, 'a') as f:
                import json
                f.write(json.dumps(scan_data) + '\n')
    
    def get_stats(self) -> Dict:
        """Get scan statistics"""
        total = len(self.memory_log)
        
        if total == 0:
            return {'total': 0, 'benign': 0, 'suspicious': 0, 'malware': 0}
        
        predictions = [s.get('prediction', 'UNKNOWN') for s in self.memory_log]
        
        return {
            'total_scans': total,
            'benign': predictions.count('BENIGN'),
            'suspicious': predictions.count('SUSPICIOUS'),
            'malware': predictions.count('MALWARE'),
            'unknown': predictions.count('UNKNOWN')
        }
