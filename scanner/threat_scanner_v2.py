#!/usr/bin/env python3
"""
Quantum-Enhanced Threat Intelligence Scanner
Simple, human-readable threat detection system
"""

import argparse
import sys
from pathlib import Path
import hashlib
import json
from datetime import datetime
from tqdm import tqdm

import numpy as np
import pickle
from typing import Dict, Any, Optional, List

import pefile
import lief

sys.path.insert(0, str(Path(__file__).parent.parent))
from threat_intelligence import ThreatIntelligence


class FileAnalyzer:
    """Analyzes files for malware indicators"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path and Path(model_path).exists():
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
    
    def compute_hashes(self, file_path: Path) -> Dict[str, str]:
        """Compute MD5, SHA1, SHA256 hashes"""
        hashes = {}
        data = file_path.read_bytes()
        
        hashes['md5'] = hashlib.md5(data).hexdigest()
        hashes['sha1'] = hashlib.sha1(data).hexdigest()
        hashes['sha256'] = hashlib.sha256(data).hexdigest()
        
        return hashes
    
    def extract_pe_features(self, file_path: Path) -> Optional[np.ndarray]:
        """Extract features from PE file"""
        try:
            binary = lief.parse(str(file_path))
            if binary is None:
                return self._generic_features(file_path)
            
            features = []
            
            # File size features
            file_size = file_path.stat().st_size
            for i in range(8):
                features.append(file_size / (10 ** (i + 1)))
            
            # Entropy
            data = file_path.read_bytes()
            entropy = self._calculate_entropy(data)
            for i in range(8):
                features.append(entropy * (i + 1) / 8)
            
            # Section count and properties
            sections = binary.sections if hasattr(binary, 'sections') else []
            for i in range(5):
                if i < len(sections):
                    features.append(sections[i].size if hasattr(sections[i], 'size') else 0)
                else:
                    features.append(0)
            
            # Pad to 16 features for model compatibility
            while len(features) < 16:
                features.append(0)
            
            return np.array(features[:16], dtype=np.float32).reshape(1, -1)
        
        except Exception as e:
            print(f"PE parsing failed: {e}, using generic features")
            return self._generic_features(file_path)
    
    def _generic_features(self, file_path: Path) -> np.ndarray:
        """Extract basic features from any file"""
        data = file_path.read_bytes()
        file_size = len(data)
        
        features = []
        
        # Byte histogram (8 buckets)
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        for i in range(8):
            start = i * 32
            end = (i + 1) * 32
            count = sum(byte_counts[start:end])
            features.append(count / max(file_size, 1))
        
        # Entropy
        entropy = self._calculate_entropy(data)
        features.append(entropy / 8.0)
        
        # File properties
        features.append(min(file_size / 1000000, 1.0))
        features.append(1.0 if data[:2] == b'MZ' else 0.0)
        features.append(1.0 if entropy > 7.0 else 0.0)
        
        # Byte patterns
        features.append(data.count(b'\x00') / max(file_size, 1))
        features.append(sum(1 for b in data if 32 <= b <= 126) / max(file_size, 1))
        
        features = features + [0.0] * (16 - len(features))
        
        return np.array(features[:16], dtype=np.float32).reshape(1, -1)
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Shannon entropy of data"""
        if not data:
            return 0.0
        
        counts = {}
        for byte in data:
            counts[byte] = counts.get(byte, 0) + 1
        
        entropy = 0.0
        data_len = len(data)
        for count in counts.values():
            p = count / data_len
            entropy -= p * np.log2(p)
        
        return entropy
    
    def predict(self, features: np.ndarray) -> tuple:
        """Predict malware probability"""
        if self.model is None:
            return "UNKNOWN", 0.0
        
        try:
            proba = self.model.predict_proba(features)[0]
            malware_prob = proba[1] if len(proba) > 1 else 0.5
            
            if malware_prob >= 0.7:
                prediction = "MALWARE"
            elif malware_prob >= 0.5:
                prediction = "SUSPICIOUS"
            else:
                prediction = "BENIGN"
            
            return prediction, malware_prob
        except Exception as e:
            print(f"Prediction error: {e}")
            return "UNKNOWN", 0.0

    def _heuristic_verdict(self, file_path: Path) -> tuple:
        """Lightweight fallback when no ML model is available"""
        data = file_path.read_bytes()
        size = len(data)
        if size == 0:
            return "BENIGN", 0.1

        entropy = self._calculate_entropy(data)
        mz = 1.0 if data[:2] == b'MZ' else 0.0
        null_ratio = data.count(b'\x00') / size
        ascii_ratio = sum(1 for b in data if 32 <= b <= 126) / size
        high_ratio = sum(1 for b in data if b >= 128) / size

        score = 0
        if entropy >= 7.2:
            score += 2
        elif entropy >= 6.7:
            score += 1

        if high_ratio >= 0.6:
            score += 1

        if null_ratio <= 0.02 and size > 200000:
            score += 1

        if mz > 0 and size < 20000:
            score += 1

        if ascii_ratio < 0.1 and mz == 0:
            score += 1

        if score >= 3:
            return "MALWARE", 0.7
        if score == 2:
            return "SUSPICIOUS", 0.6
        if score == 1:
            return "SUSPICIOUS", 0.55
        return "BENIGN", 0.35
    
    def scan_file(self, file_path: str, enable_threat_intel: bool = True) -> Dict[str, Any]:
        """Complete file scan with threat intelligence integration"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'error': 'File not found', 'file': str(file_path)}
        
        result = {
            'file': str(file_path),
            'size': file_path.stat().st_size,
            'timestamp': datetime.now().isoformat()
        }
        
        # Hashing
        result['hashes'] = self.compute_hashes(file_path)
        
        # Threat Intelligence Lookup
        threat_intel = None
        if enable_threat_intel:
            ti = ThreatIntelligence()
            threat_intel = ti.lookup_hash(result['hashes']['sha256'], 'sha256')
            result['threat_intel'] = threat_intel
        
        # Feature extraction
        features = self.extract_pe_features(file_path)
        if features is not None:
            prediction, confidence = self.predict(features)
            if prediction == "UNKNOWN":
                prediction, confidence = self._heuristic_verdict(file_path)
            result['prediction'] = prediction
            result['confidence'] = float(confidence)
            
            # Correlate with threat intelligence
            if threat_intel:
                ti = ThreatIntelligence()
                correlation = ti.correlate_with_ml(prediction, confidence, threat_intel)
                result['analysis'] = correlation
        else:
            result['prediction'] = 'UNKNOWN'
            result['confidence'] = 0.0
        
        return result
    
    def scan_directory(self, directory: str, recursive: bool = True, 
                      extensions: Optional[List[str]] = None,
                      threat_level_filter: str = 'all') -> Dict[str, Any]:
        """
        Scan entire directory for malware
        threat_level_filter: 'all', 'malware', 'suspicious', 'benign'
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return {'error': 'Directory not found', 'directory': str(directory)}
        
        if not dir_path.is_dir():
            return {'error': 'Path is not a directory', 'directory': str(directory)}
        
        results = {
            'directory': str(dir_path),
            'scan_started': datetime.now().isoformat(),
            'recursive': recursive,
            'files_scanned': 0,
            'files_found': [],
            'summary': {
                'total': 0,
                'malware': 0,
                'suspicious': 0,
                'benign': 0,
                'unknown': 0
            }
        }
        
        # Collect files to scan
        if recursive:
            files = list(dir_path.rglob('*'))
        else:
            files = list(dir_path.glob('*'))
        
        # Filter by extension if provided
        if extensions:
            extensions = [e.lower() if e.startswith('.') else f'.{e.lower()}' for e in extensions]
            files = [f for f in files if f.suffix.lower() in extensions]
        
        # Filter to regular files only
        files = [f for f in files if f.is_file()]
        
        # Scan each file with progress
        for file_path in tqdm(files, desc='Scanning files', unit='file'):
            try:
                file_result = self.scan_file(str(file_path), enable_threat_intel=True)
                
                if 'error' not in file_result:
                    results['files_scanned'] += 1
                    
                    # Extract verdict
                    verdict = file_result.get('analysis', {}).get('final_verdict', 
                                            file_result.get('prediction', 'UNKNOWN'))
                    confidence = file_result.get('analysis', {}).get('final_confidence',
                                               file_result.get('confidence', 0.0))
                    
                    # Always add to results regardless of filter
                    results['files_found'].append({
                        'file': file_path.name,
                        'path': str(file_path),
                        'size': file_result.get('size', 0),
                        'verdict': verdict,
                        'confidence': float(confidence),
                        'hashes': file_result.get('hashes', {})
                    })
                    
                    # Update summary
                    results['summary']['total'] += 1
                    if verdict == 'MALWARE':
                        results['summary']['malware'] += 1
                    elif verdict == 'SUSPICIOUS':
                        results['summary']['suspicious'] += 1
                    elif verdict == 'BENIGN':
                        results['summary']['benign'] += 1
                    else:
                        results['summary']['unknown'] += 1
                        
            except Exception as e:
                continue
        
        results['scan_completed'] = datetime.now().isoformat()
        results['total_files_found'] = len(results['files_found'])
        
        return results


class DomainAnalyzer:
    """Analyzes domains for malicious indicators"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = model_path
    
    def extract_features(self, domain: str) -> Dict[str, float]:
        """Extract domain features"""
        domain = domain.lower().split('/')[0]  # Remove path
        
        features = {}
        features['length'] = len(domain)
        features['entropy'] = self._entropy(domain)
        features['digit_ratio'] = sum(1 for c in domain if c.isdigit()) / len(domain)
        features['vowel_ratio'] = sum(1 for c in domain if c in 'aeiou') / len(domain)
        
        return features
    
    def _entropy(self, text: str) -> float:
        """Shannon entropy of text"""
        if not text:
            return 0.0
        
        counts = {}
        for char in text:
            counts[char] = counts.get(char, 0) + 1
        
        entropy = 0.0
        for count in counts.values():
            p = count / len(text)
            entropy -= p * np.log2(p)
        
        return entropy
    
    def scan_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze domain"""
        features = self.extract_features(domain)
        
        suspicious_indicators = []
        if features['entropy'] > 5.0:
            suspicious_indicators.append('high_entropy')
        if features['digit_ratio'] > 0.3:
            suspicious_indicators.append('many_digits')
        if features['length'] > 50:
            suspicious_indicators.append('long_domain')
        
        verdict = "SUSPICIOUS" if suspicious_indicators else "BENIGN"
        
        return {
            'domain': domain,
            'verdict': verdict,
            'features': features,
            'indicators': suspicious_indicators
        }


class QuantumSimulator:
    """Simple quantum-inspired anomaly detection"""
    
    def analyze(self, features: np.ndarray) -> Dict[str, Any]:
        """Analyze with quantum simulation"""
        
        # Normalize features
        f = features.flatten()
        magnitude = np.linalg.norm(f)
        
        # Entropy as anomaly measure
        f_abs = np.abs(f)
        f_norm = f_abs / (f_abs.sum() + 1e-10)
        entropy = -np.sum(f_norm * np.log(f_norm + 1e-10))
        
        # Anomaly score combination
        anomaly_score = (magnitude * entropy) / (len(f) + 1)
        confidence = 1.0 / (1.0 + anomaly_score)
        
        return {
            'anomaly_score': float(anomaly_score),
            'confidence': float(confidence),
            'magnitude': float(magnitude),
            'entropy': float(entropy)
        }


def main():
    parser = argparse.ArgumentParser(description='Quantum-Enhanced Threat Scanner')
    parser.add_argument('--file', type=str, help='File to scan')
    parser.add_argument('--directory', type=str, help='Directory to scan for malware')
    parser.add_argument('--domain', type=str, help='Domain to scan')
    parser.add_argument('--model', type=str, default='phase3/models/rf_model.pkl', help='ML model path')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--recursive', action='store_true', default=True, help='Recursively scan subdirectories')
    parser.add_argument('--extensions', type=str, help='File extensions to scan (comma-separated, e.g. exe,dll,bin)')
    parser.add_argument('--threat-level', type=str, default='all', 
                       choices=['all', 'malware', 'suspicious', 'benign'],
                       help='Filter results by threat level')
    
    args = parser.parse_args()
    
    if args.file:
        analyzer = FileAnalyzer(args.model if Path(args.model).exists() else None)
        result = analyzer.scan_file(args.file)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_file_result(result)
    
    elif args.directory:
        analyzer = FileAnalyzer(args.model if Path(args.model).exists() else None)
        extensions = None
        if args.extensions:
            extensions = [e.strip() for e in args.extensions.split(',')]
        
        result = analyzer.scan_directory(
            args.directory,
            recursive=args.recursive,
            extensions=extensions,
            threat_level_filter=args.threat_level
        )
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_directory_result(result)
    
    elif args.domain:
        analyzer = DomainAnalyzer()
        result = analyzer.scan_domain(args.domain)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_domain_result(result)
    
    else:
        parser.print_help()


def print_file_result(result: Dict[str, Any]):
    """Print file scan results"""
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
    
    print("\n" + "="*60)
    print("FILE SCAN RESULT")
    print("="*60)
    print(f"\nFile: {result['file']}")
    print(f"Size: {result['size']} bytes")
    print(f"\nHashes:")
    for hash_type, hash_val in result['hashes'].items():
        print(f"  {hash_type}: {hash_val}")
    
    print(f"\nML Analysis:")
    print(f"  Prediction: {result['prediction']}")
    print(f"  Confidence: {result['confidence']:.1%}")
    
    # Threat Intelligence
    if 'analysis' in result:
        analysis = result['analysis']
        print(f"\nThreat Intelligence:")
        print(f"  Final Verdict: {analysis['final_verdict']}")
        print(f"  Confidence: {analysis['final_confidence']:.1%}")
        print(f"  Reasoning: {analysis['reasoning']}")
        
        if analysis['virustotal_detections'] > 0:
            print(f"  VirusTotal: {analysis['virustotal_detections']}/{analysis['virustotal_total']} vendors flagged")
    
    elif 'threat_intel' in result:
        intel = result['threat_intel']
        print(f"\nThreat Intelligence:")
        vt = intel.get('sources', {}).get('virustotal', {})
        local = intel.get('sources', {}).get('database', {})
        
        if vt.get('status') == 'found':
            stats = vt.get('detections', {})
            detections = stats.get('malicious', 0) + stats.get('suspicious', 0)
            total = sum(stats.values())
            print(f"  VirusTotal: {detections}/{total} vendors detected")
        else:
            print(f"  VirusTotal: No detections (or not found)")
        
        if local.get('status') == 'found':
            print(f"  Local Database: THREAT FOUND - {local.get('threat_name')}")
        else:
            print(f"  Local Database: Not in known malware database")
    
    print("\n" + "="*60)
    print(f"VERDICT: {result.get('analysis', {}).get('final_verdict', result['prediction'])}")
    print("="*60 + "\n")


def print_directory_result(result: Dict[str, Any]):
    """Print directory scan results"""
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
    
    print("\n" + "="*80)
    print("DIRECTORY SCAN RESULTS")
    print("="*80)
    print(f"\nDirectory: {result['directory']}")
    print(f"Files Scanned: {result['files_scanned']}")
    
    summary = result['summary']
    print(f"\nSummary:")
    print(f"  Total Analyzed: {summary['total']}")
    print(f"  Malware:        {summary['malware']}")
    print(f"  Suspicious:     {summary['suspicious']}")
    print(f"  Benign:         {summary['benign']}")
    print(f"  Unknown:        {summary['unknown']}")
    
    # Sort files by verdict for better presentation
    malware_files = [f for f in result['files_found'] if f['verdict'] == 'MALWARE']
    suspicious_files = [f for f in result['files_found'] if f['verdict'] == 'SUSPICIOUS']
    benign_files = [f for f in result['files_found'] if f['verdict'] == 'BENIGN']
    unknown_files = [f for f in result['files_found'] if f['verdict'] == 'UNKNOWN']
    
    all_files = malware_files + suspicious_files + benign_files + unknown_files
    
    if all_files:
        print(f"\nFile Details:")
        print("-" * 80)
        
        idx = 1
        
        # Show malware
        if malware_files:
            print(f"\nMALWARE ({len(malware_files)}):")
            for threat in malware_files:
                print(f"  [{idx}] {threat['file']}")
                print(f"      Path:       {threat['path']}")
                print(f"      Size:       {threat['size']} bytes")
                print(f"      Confidence: {threat['confidence']:.1%}")
                print(f"      SHA256:     {threat['hashes'].get('sha256', 'N/A')[:40]}...")
                idx += 1
        
        # Show suspicious
        if suspicious_files:
            print(f"\nSUSPICIOUS ({len(suspicious_files)}):")
            for threat in suspicious_files:
                print(f"  [{idx}] {threat['file']}")
                print(f"      Path:       {threat['path']}")
                print(f"      Size:       {threat['size']} bytes")
                print(f"      Confidence: {threat['confidence']:.1%}")
                print(f"      SHA256:     {threat['hashes'].get('sha256', 'N/A')[:40]}...")
                idx += 1
        
        # Show benign
        if benign_files:
            print(f"\nBENIGN ({len(benign_files)}):")
            for threat in benign_files:
                print(f"  [{idx}] {threat['file']}")
                print(f"      Path:       {threat['path']}")
                print(f"      Size:       {threat['size']} bytes")
                print(f"      Confidence: {threat['confidence']:.1%}")
                print(f"      SHA256:     {threat['hashes'].get('sha256', 'N/A')[:40]}...")
                idx += 1
        
        # Show unknown
        if unknown_files:
            print(f"\nUNKNOWN ({len(unknown_files)}):")
            for threat in unknown_files:
                print(f"  [{idx}] {threat['file']}")
                print(f"      Path:       {threat['path']}")
                print(f"      Size:       {threat['size']} bytes")
                print(f"      Confidence: {threat['confidence']:.1%}")
                print(f"      SHA256:     {threat['hashes'].get('sha256', 'N/A')[:40]}...")
                idx += 1
    else:
        print(f"\nNo files scanned.")
    
    print("\n" + "="*80)
    print(f"Scan Duration: {result.get('scan_completed', 'N/A')}")
    print("="*80 + "\n")


def print_domain_result(result: Dict[str, Any]):
    """Print domain scan results"""
    print("\n" + "="*60)
    print("DOMAIN SCAN RESULT")
    print("="*60)
    print(f"\nDomain: {result['domain']}")
    print(f"Verdict: {result['verdict']}")
    
    if result['indicators']:
        print(f"\nSuspicious Indicators:")
        for ind in result['indicators']:
            print(f"  - {ind}")
    
    print(f"\nFeatures:")
    for key, val in result['features'].items():
        print(f"  {key}: {val:.3f}")
    
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
