"""
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
