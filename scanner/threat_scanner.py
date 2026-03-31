#!/usr/bin/env python3
"""
Quantum-Enhanced Threat Scanner - Main CLI Application
Production-grade malware and DGA domain detection tool.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.modules.file_scanner import FileScanner
from scanner.modules.domain_scanner import DomainScanner
from scanner.modules.quantum_analyzer import QuantumAnalyzer
from scanner.core.logger import get_logger
from scanner.config.config import Colors, CONFIDENCE_THRESHOLD


class ThreatScanner:
    """Main threat scanner application"""
    
    def __init__(self, vt_api_key: Optional[str] = None, offline_mode: bool = False):
        """
        Initialize threat scanner.
        
        Args:
            vt_api_key: VirusTotal API key
            offline_mode: Run in offline mode (no API calls)
        """
        self.vt_api_key = vt_api_key
        self.offline_mode = offline_mode
        
        # Initialize scanners
        print(f"\n{Colors.BOLD}{Colors.HEADER}╔═══════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}║   Quantum-Enhanced Threat Intelligence Scanner v1.0      ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}╚═══════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        if offline_mode:
            print(f"{Colors.WARNING}⚙ Running in OFFLINE mode (API lookups disabled){Colors.ENDC}\n")
        
        self.file_scanner = FileScanner(vt_api_key=vt_api_key, offline_mode=offline_mode)
        self.domain_scanner = DomainScanner(offline_mode=offline_mode)
        self.quantum_analyzer = QuantumAnalyzer()
        self.logger = get_logger()
    
    def scan_file(self, file_path: str, auto_quantum: bool = True):
        """
        Scan a file for malware.
        
        Args:
            file_path: Path to file to scan
            auto_quantum: Automatically run quantum analysis if confidence is low
        """
        # Perform file scan
        results = self.file_scanner.scan_file(file_path)
        
        if 'error' in results:
            print(f"\n{Colors.FAIL}✗ Error: {results['error']}{Colors.ENDC}")
            return
        
        # Display results
        self._display_file_results(results)
        
        # Quantum analysis if needed
        quantum_results = None
        if auto_quantum and results.get('needs_quantum_analysis'):
            print(f"\n{Colors.WARNING}⚡ Initiating quantum analysis due to low confidence...{Colors.ENDC}")
            
            # Get features (we'd need to extract them again or save them)
            features = self.file_scanner.extract_pe_features(Path(file_path))
            if features is not None:
                quantum_results = self.quantum_analyzer.analyze(features)
        
        # Log scan
        self._log_file_scan(results, quantum_results)
        
        # Final verdict
        self._print_final_verdict(results, quantum_results)
    
    def scan_domain(self, domain: str, auto_quantum: bool = True):
        """
        Scan a domain for malicious activity.
        
        Args:
            domain: Domain name or URL to scan
            auto_quantum: Automatically run quantum analysis if confidence is low
        """
        # Perform domain scan
        results = self.domain_scanner.scan_domain(domain)
        
        # Display results
        self._display_domain_results(results)
        
        # Quantum analysis if needed
        quantum_results = None
        if auto_quantum and results.get('needs_quantum_analysis'):
            print(f"\n{Colors.WARNING}⚡ Initiating quantum analysis due to low confidence...{Colors.ENDC}")
            
            # Extract features and analyze
            feature_vector, feature_dict = self.domain_scanner.extract_domain_features(domain)
            
            if feature_dict:
                qsvc_features = [
                    feature_dict.get('length', 0),
                    feature_dict.get('entropy', 0),
                    feature_dict.get('vowel_ratio', 0),
                    feature_dict.get('digit_ratio', 0)
                ]
                import numpy as np
                if len(qsvc_features) == 4:
                    X_q = np.array(qsvc_features).reshape(1, -1)
                    quantum_results = self.quantum_analyzer.analyze(X_q)
                else:
                    print(f"{Colors.WARNING}⚠ Quantum feature mismatch. Skipping QSVC.{Colors.ENDC}")
        
        # Log scan
        self._log_domain_scan(results, quantum_results)
        
        # Final verdict
        self._print_final_verdict(results, quantum_results)
    
    def batch_scan_domains(self, domain_file: str):
        """
        Scan multiple domains from a file.
        
        Args:
            domain_file: Path to file containing domains (one per line)
        """
        try:
            with open(domain_file, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            print(f"\n{Colors.BOLD}Loaded {len(domains)} domains from {domain_file}{Colors.ENDC}")
            
            for i, domain in enumerate(domains, 1):
                print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
                print(f"{Colors.BOLD}Domain {i}/{len(domains)}{Colors.ENDC}")
                print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
                self.scan_domain(domain, auto_quantum=False)  # Disable auto-quantum for batch
        
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error reading domain file: {e}{Colors.ENDC}")
    
    def show_statistics(self):
        """Display scan statistics"""
        stats = self.logger.get_statistics()
        
        print(f"\n{Colors.BOLD}{Colors.HEADER}╔═══════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}║                  Scan Statistics                          ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}╚═══════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"Total Scans:        {stats.get('total_scans', 0)}")
        print(f"  File Scans:       {stats.get('file_scans', 0)}")
        print(f"  Domain Scans:     {stats.get('domain_scans', 0)}")
        print(f"\nDetections:")
        print(f"  {Colors.FAIL}Malicious:        {stats.get('malicious_detected', 0)}{Colors.ENDC}")
        print(f"  {Colors.OKGREEN}Benign:           {stats.get('benign_detected', 0)}{Colors.ENDC}")
        print(f"  {Colors.WARNING}Suspicious:       {stats.get('suspicious_detected', 0)}{Colors.ENDC}")
        print(f"\nQuantum Analyses:   {stats.get('quantum_analyses', 0)}\n")
    
    def _display_file_results(self, results: dict):
        """Display file scan results"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}SCAN RESULTS{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
        
        # ML Results
        if results.get('ml_prediction'):
            prediction = results['ml_prediction']
            confidence = results['ml_confidence']
            
            if prediction == 'MALICIOUS':
                color = Colors.FAIL
                icon = '❌'
            else:
                color = Colors.OKGREEN
                icon = '✅'
            
            print(f"{Colors.BOLD}ML Analysis:{Colors.ENDC}")
            print(f"  Prediction: {color}{icon} {prediction}{Colors.ENDC}")
            print(f"  Confidence: {confidence:.2%}")
        
        # VirusTotal Results
        if results.get('virustotal'):
            vt = results['virustotal']
            print(f"\n{Colors.BOLD}VirusTotal:{Colors.ENDC}")
            print(f"  Detections: {vt['malicious']}/{vt['total_engines']}")
            
            if vt['malicious'] > 0:
                print(f"  {Colors.FAIL}⚠ Flagged by {vt['malicious']} security engines{Colors.ENDC}")
    
    def _display_domain_results(self, results: dict):
        """Display domain scan results"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}SCAN RESULTS{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
        
        if results.get('ml_prediction'):
            prediction = results['ml_prediction']
            confidence = results['ml_confidence']
            
            if prediction == 'MALICIOUS':
                color = Colors.FAIL
                icon = '❌'
            else:
                color = Colors.OKGREEN
                icon = '✅'
            
            print(f"{Colors.BOLD}ML Analysis:{Colors.ENDC}")
            print(f"  Prediction: {color}{icon} {prediction}{Colors.ENDC}")
            print(f"  Confidence: {confidence:.2%}")
    
    def _print_final_verdict(self, results: dict, quantum_results: Optional[dict] = None):
        """Print final scan verdict"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}FINAL VERDICT{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
        
        # Determine final verdict
        ml_pred = results.get('ml_prediction', 'UNKNOWN')
        ml_conf = results.get('ml_confidence', 0.0)
        
        if quantum_results:
            q_conf = quantum_results.get('confidence', quantum_results.get('quantum_confidence', 0.0))
            final_confidence = (ml_conf * 0.7) + (q_conf * 0.3)
            
            if final_confidence >= 0.7:
                verdict = 'THREAT DETECTED'
                color = Colors.FAIL
                icon = '🚨'
            elif final_confidence >= 0.5:
                verdict = 'SUSPICIOUS (Ensemble)'
                color = Colors.WARNING
                icon = '⚠'
            else:
                verdict = 'BENIGN'
                color = Colors.OKGREEN
                icon = '✅'
            print(f"  Ensemble Confidence: {final_confidence:.2%}\n")
        else:
            if ml_pred == 'MALICIOUS':
                verdict = 'THREAT DETECTED'
                color = Colors.FAIL
                icon = '🚨'
            elif ml_pred == 'SUSPICIOUS':
                verdict = 'SUSPICIOUS'
                color = Colors.WARNING
                icon = '⚠'
            else:
                verdict = 'BENIGN'
                color = Colors.OKGREEN
                icon = '✅'
        
        print(f"{color}{Colors.BOLD}{icon} {verdict}{Colors.ENDC}\n")
    
    def _log_file_scan(self, results: dict, quantum_results: Optional[dict] = None):
        """Log file scan to database"""
        scan_data = {
            'scan_type': 'file',
            'target': results.get('file_path', ''),
            'result': results.get('ml_prediction', 'UNKNOWN'),
            'confidence': results.get('ml_confidence', 0.0),
            'ml_prediction': results.get('ml_prediction', ''),
            'quantum_analysis': quantum_results,
            'vt_detections': results.get('virustotal', {}).get('malicious', 0) if results.get('virustotal') else None,
            'file_hash': results.get('hashes', {}).get('sha256', ''),
            'additional_info': {
                'file_size_mb': results.get('file_size_mb', 0),
                'hashes': results.get('hashes', {})
            }
        }
        
        self.logger.log_scan(scan_data)
    
    def _log_domain_scan(self, results: dict, quantum_results: Optional[dict] = None):
        """Log domain scan to database"""
        scan_data = {
            'scan_type': 'domain',
            'target': results.get('domain', ''),
            'result': results.get('ml_prediction', 'UNKNOWN'),
            'confidence': results.get('ml_confidence', 0.0),
            'ml_prediction': results.get('ml_prediction', ''),
            'quantum_analysis': quantum_results,
            'vt_detections': None,
            'file_hash': None,
            'additional_info': {
                'features': results.get('features', {})
            }
        }
        
        self.logger.log_scan(scan_data)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Quantum-Enhanced Threat Intelligence Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a file
  python threat_scanner.py --file malware.exe
  
  # Scan a file with VirusTotal lookup
  python threat_scanner.py --file malware.exe --vt-key YOUR_API_KEY
  
  # Scan a domain
  python threat_scanner.py --domain example.com
  
  # Batch scan domains from file
  python threat_scanner.py --domain-file domains.txt
  
  # Show statistics
  python threat_scanner.py --stats
  
  # Offline mode (no API calls)
  python threat_scanner.py --file malware.exe --offline
        """
    )
    
    # Scan targets
    parser.add_argument('--file', '-f', type=str, help='File to scan')
    parser.add_argument('--domain', '-d', type=str, help='Domain or URL to scan')
    parser.add_argument('--domain-file', type=str, help='File containing domains to scan (one per line)')
    
    # Options
    parser.add_argument('--vt-key', type=str, help='VirusTotal API key')
    parser.add_argument('--offline', action='store_true', help='Run in offline mode (no API calls)')
    parser.add_argument('--no-quantum', action='store_true', help='Disable automatic quantum analysis')
    parser.add_argument('--stats', action='store_true', help='Show scan statistics')
    
    args = parser.parse_args()
    
    # Check if any action specified
    if not any([args.file, args.domain, args.domain_file, args.stats]):
        parser.print_help()
        sys.exit(0)
    
    # Get API key from environment if not provided
    vt_api_key = args.vt_key or os.environ.get('VT_API_KEY')
    
    # Initialize scanner
    scanner = ThreatScanner(vt_api_key=vt_api_key, offline_mode=args.offline)
    
    # Execute requested action
    try:
        if args.stats:
            scanner.show_statistics()
        
        elif args.file:
            scanner.scan_file(args.file, auto_quantum=not args.no_quantum)
        
        elif args.domain:
            scanner.scan_domain(args.domain, auto_quantum=not args.no_quantum)
        
        elif args.domain_file:
            scanner.batch_scan_domains(args.domain_file)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠ Scan interrupted by user{Colors.ENDC}")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n{Colors.FAIL}✗ Fatal error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
