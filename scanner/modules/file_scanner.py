"""
File scanner module for malware detection.
Handles file hashing, VirusTotal API integration, and PE feature extraction.
"""

import hashlib
import os
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests
import pickle
import numpy as np

try:
    import pefile
    import lief
    PEFILE_AVAILABLE = True
except ImportError:
    PEFILE_AVAILABLE = False

from ..config.config import (
    EMBER_MODEL_PATH, VIRUSTOTAL_API_URL, MAX_FILE_SIZE_MB,
    SUPPORTED_FILE_TYPES, CONFIDENCE_THRESHOLD, MALWARE_THRESHOLD,
    Colors
)


class FileScanner:
    """Handles file scanning for malware detection"""
    
    def __init__(self, vt_api_key: Optional[str] = None, offline_mode: bool = False):
        """
        Initialize file scanner.
        
        Args:
            vt_api_key: VirusTotal API key (optional)
            offline_mode: If True, skip all API calls
        """
        self.vt_api_key = vt_api_key
        self.offline_mode = offline_mode
        self.ml_model = None
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
        """
        Calculate MD5, SHA1, and SHA256 hashes of a file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Dictionary containing hash values
        """
        md5_hash = hashlib.md5()
        sha1_hash = hashlib.sha1()
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
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
        """
        Check file hash against VirusTotal API.
        
        Args:
            file_hash: SHA256 hash of the file
        
        Returns:
            Dictionary containing VirusTotal results or None
        """
        if self.offline_mode:
            print(f"{Colors.OKCYAN}ℹ Offline mode: Skipping VirusTotal lookup{Colors.ENDC}")
            return None
        
        if not self.vt_api_key:
            print(f"{Colors.OKCYAN}ℹ No VirusTotal API key provided{Colors.ENDC}")
            return None
        
        try:
            url = VIRUSTOTAL_API_URL.format(hash=file_hash)
            headers = {
                'x-apikey': self.vt_api_key
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
                
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'undetected': stats.get('undetected', 0),
                    'harmless': stats.get('harmless', 0),
                    'total_engines': sum(stats.values()),
                    'permalink': data.get('data', {}).get('links', {}).get('self', '')
                }
            elif response.status_code == 404:
                print(f"{Colors.OKCYAN}ℹ File not found in VirusTotal database{Colors.ENDC}")
                return None
            else:
                print(f"{Colors.WARNING}⚠ VirusTotal API error: {response.status_code}{Colors.ENDC}")
                return None
        except requests.exceptions.Timeout:
            print(f"{Colors.WARNING}⚠ VirusTotal request timed out{Colors.ENDC}")
            return None
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Error querying VirusTotal: {e}{Colors.ENDC}")
            return None
    
    def extract_pe_features(self, file_path: Path) -> Optional[np.ndarray]:
        """
        Extract static features from a PE file using pefile/lief.
        Falls back to generic features for non-PE files.
        
        Args:
            file_path: Path to the PE file
        
        Returns:
            Feature vector as numpy array or None
        """
        if not PEFILE_AVAILABLE:
            print(f"{Colors.WARNING}⚠ pefile/lief not available. Install with: pip install pefile lief{Colors.ENDC}")
            return None
        
        try:
            # Try using LIEF first (more robust)
            binary = lief.parse(str(file_path))
            if binary is None:
                print(f"{Colors.WARNING}⚠ Not a valid PE file, using generic features{Colors.ENDC}")
                return self._extract_generic_features(file_path)
            
            features = self._extract_lief_features(binary)
            return features
        
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Error extracting PE features, using generic features{Colors.ENDC}")
            
            # Try fallback to generic features for non-PE files
            try:
                return self._extract_generic_features(file_path)
            except Exception as e2:
                print(f"{Colors.FAIL}✗ Could not extract any features: {e2}{Colors.ENDC}")
                return None
    
    def _extract_lief_features(self, binary) -> np.ndarray:
        """
        Extract features using LIEF library.
        Returns a simplified feature vector compatible with the model.
        """
        features = []
        
        # File size and entropy features (histogram approximation)
        file_size = binary.virtual_size if hasattr(binary, 'virtual_size') else 0
        for i in range(10):
            features.append(file_size / (10 ** (i + 1)))  # Histogram approximation
        
        # Byte entropy (approximation)
        entropy = binary.entropy if hasattr(binary, 'entropy') else 0
        for i in range(10):
            features.append(entropy * (i + 1) / 10)
        
        # Section features
        sections = binary.sections if hasattr(binary, 'sections') else []
        section_count = min(len(sections), 5)
        for i in range(5):
            if i < section_count:
                sec = sections[i]
                features.append(sec.size if hasattr(sec, 'size') else 0)
            else:
                features.append(0)
        
        # Import features
        imports = []
        if hasattr(binary, 'imports'):
            for imp in binary.imports:
                if hasattr(imp, 'entries'):
                    imports.extend(imp.entries)
        import_count = min(len(imports), 5)
        for i in range(5):
            features.append(import_count if i < import_count else 0)
        
        # Export features
        exports = binary.exported_functions if hasattr(binary, 'exported_functions') else []
        export_count = min(len(exports), 2)
        for i in range(2):
            features.append(export_count if i < export_count else 0)
        
        # General features
        features.extend([
            1 if binary.has_signature else 0,
            len(sections),
            import_count,
            export_count,
            file_size
        ])
        
        # Ensure we have exactly 37 features (to match EMBER model)
        while len(features) < 37:
            features.append(0)
        features = features[:37]
        
        return np.array(features, dtype=np.float32).reshape(1, -1)
    
    def _extract_pefile_features(self, pe) -> np.ndarray:
        """
        Extract features using pefile library.
        Returns a simplified feature vector.
        """
        features = []
        
        # Histogram features (approximation)
        for i in range(10):
            features.append(len(pe.sections) * (i + 1) if pe.sections else 0)
        
        # Entropy features
        for i in range(10):
            if pe.sections and len(pe.sections) > 0:
                entropy = pe.sections[0].get_entropy() if hasattr(pe.sections[0], 'get_entropy') else 0
                features.append(entropy * (i + 1) / 10)
            else:
                features.append(0)
        
        # Section features
        for i in range(5):
            if pe.sections and i < len(pe.sections):
                features.append(pe.sections[i].SizeOfRawData)
            else:
                features.append(0)
        
        # Import features
        import_count = 0
        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                import_count += len(entry.imports)
        for i in range(5):
            features.append(import_count if i < 5 else 0)
        
        # Export features
        export_count = 0
        if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
            export_count = len(pe.DIRECTORY_ENTRY_EXPORT.symbols)
        for i in range(2):
            features.append(export_count)
        
        # General features
        features.extend([
            1 if hasattr(pe, 'DIRECTORY_ENTRY_SECURITY') else 0,
            len(pe.sections) if pe.sections else 0,
            import_count,
            export_count,
            pe.OPTIONAL_HEADER.SizeOfImage if hasattr(pe, 'OPTIONAL_HEADER') else 0
        ])
        
        # Ensure exactly 37 features
        while len(features) < 37:
            features.append(0)
        features = features[:37]
        
        return np.array(features, dtype=np.float32).reshape(1, -1)
    
    def _extract_generic_features(self, file_path: Path) -> np.ndarray:
        """
        Extract generic features from any file (PE or non-PE).
        Uses 16 features to match EMBER model input size.
        Returns feature counts similar to what pefile/lief would return.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Feature vector as numpy array (16 features for EMBER model)
        """
        features = []
        
        try:
            # Read file
            file_data = file_path.read_bytes()
            file_size = len(file_data)
            
            # Compute byte frequency histogram
            byte_counts = [0] * 256
            for byte in file_data:
                byte_counts[byte] += 1
            
            # Calculate entropy
            entropy = 0.0
            file_len = len(file_data)
            if file_len > 0:
                for count in byte_counts:
                    if count > 0:
                        p = count / file_len
                        entropy -= p * (math.log2(p) if p > 0 else 0)
            
            # EMBER expects 16 features derived from PE file
            # We'll generate approximations from file content analysis
            
            # Features 0-7: Histogram of byte values (first 8 buckets)
            hist_buckets = 8
            bytes_per_bucket = 256 // hist_buckets
            for i in range(hist_buckets):
                start = i * bytes_per_bucket
                end = (i + 1) * bytes_per_bucket
                bucket_sum = sum(byte_counts[start:end])
                features.append(bucket_sum / max(file_len, 1))
            
            # Features 8-11: Entropy and size-based features
            features.append(entropy / 8.0)  # Normalized entropy
            features.append(min(file_size / 10000.0, 1.0))  # Size feature (normalized)
            features.append(1.0 if file_data[:2] == b'MZ' else 0.0)  # PE header detector
            features.append(1.0 if entropy > 7.0 else 0.0)  # High entropy flag
            
            # Features 12-15: Byte pattern features
            null_count = file_data.count(b'\x00')
            features.append(null_count / max(file_len, 1))  # Null byte ratio
            
            printable = sum(1 for b in file_data if 32 <= b <= 126 or b in (9, 10, 13))
            features.append(printable / max(file_len, 1))  # ASCII ratio
            
            # High byte (0x80-0xFF) ratio
            high_bytes = sum(1 for b in file_data if b >= 128)
            features.append(high_bytes / max(file_len, 1))
            
            # Diversity (unique bytes / total)
            unique_bytes = len(set(file_data))
            features.append(unique_bytes / 256.0)
            
            # Ensure we have exactly 16 features
            while len(features) < 16:
                features.append(0.0)
            features = features[:16]
            
            return np.array(features, dtype=np.float32).reshape(1, -1)
        
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Error extracting generic features: {e}{Colors.ENDC}")
            # Return default zero features (16 features)
            return np.zeros((1, 16), dtype=np.float32)
    
    def predict_malware(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict if features indicate malware using ML model.
        
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
            
            # Assuming class 1 is malware, class 0 is benign
            malware_prob = proba[1] if len(proba) > 1 else proba[0]
            
            # Determine prediction
            if malware_prob >= MALWARE_THRESHOLD:
                prediction = "MALICIOUS"
            else:
                prediction = "BENIGN"
            
            return prediction, float(malware_prob)
        
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error during prediction: {e}{Colors.ENDC}")
            return "UNKNOWN", 0.0
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Perform complete file scan including hashing, VT lookup, and ML analysis.
        
        Args:
            file_path: Path to file to scan
        
        Returns:
            Dictionary containing complete scan results
        """
        file_path = Path(file_path)
        
        # Validate file
        if not file_path.exists():
            return {
                'error': 'File not found',
                'file_path': str(file_path)
            }
        
        if not file_path.is_file():
            return {
                'error': 'Path is not a file',
                'file_path': str(file_path)
            }
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return {
                'error': f'File too large ({file_size_mb:.2f} MB > {MAX_FILE_SIZE_MB} MB)',
                'file_path': str(file_path)
            }
        
        print(f"\n{Colors.BOLD}Scanning file: {file_path.name}{Colors.ENDC}")
        print(f"File size: {file_size_mb:.2f} MB\n")
        
        results = {
            'file_path': str(file_path),
            'file_size_mb': file_size_mb,
            'hashes': {},
            'virustotal': None,
            'ml_prediction': None,
            'ml_confidence': 0.0,
            'needs_quantum_analysis': False
        }
        
        # Step 1: Hash the file
        print(f"{Colors.OKCYAN}[1/4] Computing file hashes...{Colors.ENDC}")
        hashes = self.hash_file(file_path)
        results['hashes'] = hashes
        
        if hashes:
            print(f"  MD5:    {hashes.get('md5', 'N/A')}")
            print(f"  SHA1:   {hashes.get('sha1', 'N/A')}")
            print(f"  SHA256: {hashes.get('sha256', 'N/A')}\n")
        
        # Step 2: Check VirusTotal
        print(f"{Colors.OKCYAN}[2/4] Checking VirusTotal...{Colors.ENDC}")
        if hashes.get('sha256'):
            vt_results = self.check_virustotal(hashes['sha256'])
            results['virustotal'] = vt_results
            
            if vt_results:
                print(f"  Detections: {vt_results['malicious']}/{vt_results['total_engines']}")
                if vt_results['malicious'] > 0:
                    print(f"  {Colors.FAIL}⚠ File flagged by {vt_results['malicious']} engines{Colors.ENDC}")
                else:
                    print(f"  {Colors.OKGREEN}✓ No detections{Colors.ENDC}")
        print()
        
        # Step 3: Extract PE features
        print(f"{Colors.OKCYAN}[3/4] Extracting PE features...{Colors.ENDC}")
        features = self.extract_pe_features(file_path)
        
        if features is not None:
            print(f"  {Colors.OKGREEN}✓ Extracted {features.shape[1]} features{Colors.ENDC}\n")
        else:
            print(f"  {Colors.WARNING}⚠ Could not extract features{Colors.ENDC}\n")
        
        # Step 4: ML prediction
        print(f"{Colors.OKCYAN}[4/4] Running ML analysis...{Colors.ENDC}")
        if features is not None:
            prediction, confidence = self.predict_malware(features)
            results['ml_prediction'] = prediction
            results['ml_confidence'] = confidence
            
            # Check if quantum analysis needed
            if confidence < CONFIDENCE_THRESHOLD:
                results['needs_quantum_analysis'] = True
                print(f"  {Colors.WARNING}⚠ Low confidence ({confidence:.2%}) - Quantum analysis recommended{Colors.ENDC}")
            else:
                print(f"  Prediction: {prediction} (confidence: {confidence:.2%})")
        
        return results
