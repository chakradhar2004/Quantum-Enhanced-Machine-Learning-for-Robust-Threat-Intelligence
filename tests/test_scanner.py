"""
Unit tests for Quantum-Enhanced Threat Scanner
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.modules.domain_scanner import DomainScanner
from scanner.modules.file_scanner import FileScanner
from scanner.modules.quantum_analyzer import QuantumAnalyzer
import numpy as np


class TestDomainScanner(unittest.TestCase):
    """Test domain scanning functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scanner = DomainScanner(offline_mode=True)
    
    def test_domain_entropy(self):
        """Test entropy calculation"""
        # Simple test case
        entropy = self.scanner.domain_entropy("aaaa")
        self.assertEqual(entropy, 0.0)  # All same characters = 0 entropy
        
        # Mixed characters should have higher entropy
        entropy2 = self.scanner.domain_entropy("abcd")
        self.assertGreater(entropy2, 0.0)
    
    def test_vowel_ratio(self):
        """Test vowel ratio calculation"""
        ratio = self.scanner.vowel_ratio("aeiou")
        self.assertEqual(ratio, 1.0)  # All vowels
        
        ratio2 = self.scanner.vowel_ratio("bcdfg")
        self.assertEqual(ratio2, 0.0)  # No vowels
    
    def test_digit_ratio(self):
        """Test digit ratio calculation"""
        ratio = self.scanner.digit_ratio("12345")
        self.assertEqual(ratio, 1.0)  # All digits
        
        ratio2 = self.scanner.digit_ratio("abcde")
        self.assertEqual(ratio2, 0.0)  # No digits
    
    def test_feature_extraction(self):
        """Test domain feature extraction"""
        features, feature_dict = self.scanner.extract_domain_features("google.com")
        
        # Check feature vector shape
        self.assertEqual(features.shape, (1, 5))
        
        # Check feature dictionary has all keys
        expected_keys = ['length', 'entropy', 'vowel_ratio', 'digit_ratio', 'consonant_ratio']
        for key in expected_keys:
            self.assertIn(key, feature_dict)
    
    def test_url_parsing(self):
        """Test URL parsing in domain extraction"""
        # Test with full URL
        features1, _ = self.scanner.extract_domain_features("https://example.com/path")
        features2, _ = self.scanner.extract_domain_features("example.com")
        
        # Both should extract 'example' as the domain
        # Features should be similar (not necessarily identical due to processing)
        self.assertEqual(features1.shape, features2.shape)


class TestFileScanner(unittest.TestCase):
    """Test file scanning functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scanner = FileScanner(offline_mode=True)
    
    def test_hash_calculation(self):
        """Test file hashing"""
        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("test content")
            temp_file = Path(f.name)
        
        try:
            hashes = self.scanner.hash_file(temp_file)
            
            # Check all hash types are present
            self.assertIn('md5', hashes)
            self.assertIn('sha1', hashes)
            self.assertIn('sha256', hashes)
            
            # Check hash format (hexadecimal strings)
            self.assertEqual(len(hashes['md5']), 32)
            self.assertEqual(len(hashes['sha1']), 40)
            self.assertEqual(len(hashes['sha256']), 64)
        
        finally:
            # Clean up
            temp_file.unlink()
    
    def test_virustotal_offline(self):
        """Test VirusTotal in offline mode"""
        result = self.scanner.check_virustotal("fake_hash")
        self.assertIsNone(result)  # Should return None in offline mode


class TestQuantumAnalyzer(unittest.TestCase):
    """Test quantum analysis functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = QuantumAnalyzer(use_quantum=True)
    
    def test_feature_preprocessing(self):
        """Test feature preprocessing"""
        # Create test features
        features = np.array([1, 2, 3, 4, 5])
        
        processed = self.analyzer.preprocess_features(features)
        
        # Check shape
        self.assertEqual(processed.ndim, 2)
        self.assertEqual(processed.shape[1], 5)
    
    def test_quantum_simulation(self):
        """Test quantum circuit simulation"""
        features = np.random.rand(1, 10)
        
        results = self.analyzer.quantum_circuit_simulation(features)
        
        # Check required keys
        self.assertIn('anomaly_score', results)
        self.assertIn('quantum_confidence', results)
        self.assertIn('anomaly_level', results)
        self.assertIn('is_anomalous', results)
        
        # Check value ranges
        self.assertGreaterEqual(results['anomaly_score'], 0)
        self.assertGreaterEqual(results['quantum_confidence'], 0)
        self.assertLessEqual(results['quantum_confidence'], 1)
    
    def test_analyze_method(self):
        """Test main analyze method"""
        features = np.random.rand(10)
        
        results = self.analyzer.analyze(features, method='simulation')
        
        # Check essential keys
        self.assertIn('method', results)
        self.assertIn('is_anomalous', results)
        self.assertEqual(results['method'], 'quantum_simulation')


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_domain_scan_workflow(self):
        """Test complete domain scan workflow"""
        scanner = DomainScanner(offline_mode=True)
        
        # Scan a known benign domain
        results = scanner.scan_domain("google.com")
        
        # Check results structure
        self.assertIn('domain', results)
        self.assertIn('features', results)
        self.assertIn('ml_prediction', results)
        self.assertIn('ml_confidence', results)
    
    def test_feature_consistency(self):
        """Test that same input produces same features"""
        scanner = DomainScanner(offline_mode=True)
        
        features1, _ = scanner.extract_domain_features("test.com")
        features2, _ = scanner.extract_domain_features("test.com")
        
        np.testing.assert_array_equal(features1, features2)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    print("Running Quantum-Enhanced Threat Scanner Tests\n")
    print("=" * 60)
    run_tests()
