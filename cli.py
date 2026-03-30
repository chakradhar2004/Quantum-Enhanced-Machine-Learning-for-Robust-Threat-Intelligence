#!/usr/bin/env python3
"""
Quantum-Enhanced Threat Intelligence — Unified CLI

SINGLE entry point for all scanner operations.
Replaces: main.py, scanner/threat_scanner.py, scanner/threat_scanner_v2.py,
           simulation.py, phase3/phase3_main.py
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

# Project imports
from config import (
    Colors, VT_API_KEY, MODEL_DIR, QUANTUM_MODEL_DIR,
    DOMAIN_MODEL_PATH, EMBER_MODEL_PATH, QSVC_MODEL_PATH,
    CONFIDENCE_THRESHOLD, MALWARE_THRESHOLD, MAX_FILE_SIZE_MB,
)
from utils.features import DomainFeatureExtractor, FileFeatureExtractor
from utils.model_loader import SafeModelLoader
from utils.validators import (
    validate_file_path, validate_directory_path,
    validate_domain, validate_hash, ValidationError,
)

logger = logging.getLogger('cli')


# ─────────────────────────────────────────────────────
# Scanner Engine
# ─────────────────────────────────────────────────────

class ThreatEngine:
    """Core threat detection engine used by all CLI commands."""

    def __init__(self, offline: bool = False):
        self.offline = offline
        self.domain_extractor = DomainFeatureExtractor(use_legacy=True)
        self.file_extractor = FileFeatureExtractor()

        # Load models
        self.loader = SafeModelLoader(str(MODEL_DIR))
        self.domain_model = None
        self.ember_model = None
        self.qsvc_model = None

        self._load_models()

    def _load_models(self):
        """Load all available models."""
        # Domain RF
        try:
            if DOMAIN_MODEL_PATH.exists():
                self.domain_model = self.loader.load(
                    DOMAIN_MODEL_PATH.name, verify=False
                )
                logger.info("Loaded domain RF model ✓")
        except Exception as e:
            logger.warning(f"Could not load domain model: {e}")

        # EMBER RF
        try:
            if EMBER_MODEL_PATH.exists():
                self.ember_model = self.loader.load(
                    EMBER_MODEL_PATH.name, verify=False
                )
                logger.info("Loaded EMBER RF model ✓")
        except Exception as e:
            logger.warning(f"Could not load EMBER model: {e}")

        # Quantum QSVC
        try:
            q_loader = SafeModelLoader(str(QUANTUM_MODEL_DIR))
            if QSVC_MODEL_PATH.exists():
                self.qsvc_model = q_loader.load(
                    QSVC_MODEL_PATH.name, verify=False
                )
                logger.info("Loaded QSVC quantum model ✓")
        except Exception as e:
            logger.warning(f"Could not load QSVC model: {e}")

    def scan_domain(self, domain: str) -> dict:
        """Scan a domain for DGA indicators."""
        domain = validate_domain(domain)
        features, feature_dict = self.domain_extractor.extract(domain)

        result = {
            'type': 'domain',
            'target': domain,
            'features': feature_dict,
            'timestamp': datetime.now().isoformat(),
            'prediction': 'UNKNOWN',
            'confidence': 0.0,
        }

        if self.domain_model is not None:
            try:
                proba = self.domain_model.predict_proba(features)[0]
                malicious_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
                result['prediction'] = (
                    'MALICIOUS' if malicious_prob >= MALWARE_THRESHOLD else 'BENIGN'
                )
                result['confidence'] = malicious_prob
            except Exception as e:
                logger.error(f"Domain prediction failed: {e}")
        else:
            result['prediction'] = 'UNKNOWN'
            result['note'] = 'No domain model loaded'

        return result

    def scan_file(self, file_path: str) -> dict:
        """Scan a file for malware indicators."""
        import hashlib

        path = validate_file_path(file_path, max_size_mb=MAX_FILE_SIZE_MB)

        # Compute hashes
        data = path.read_bytes()
        hashes = {
            'md5': hashlib.md5(data).hexdigest(),
            'sha1': hashlib.sha1(data).hexdigest(),
            'sha256': hashlib.sha256(data).hexdigest(),
        }

        result = {
            'type': 'file',
            'target': str(path),
            'size_bytes': len(data),
            'hashes': hashes,
            'timestamp': datetime.now().isoformat(),
            'prediction': 'UNKNOWN',
            'confidence': 0.0,
        }

        # Extract features
        features = self.file_extractor.extract(path)
        if features is not None and self.ember_model is not None:
            try:
                proba = self.ember_model.predict_proba(features)[0]
                malware_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
                result['prediction'] = (
                    'MALICIOUS' if malware_prob >= MALWARE_THRESHOLD else 'BENIGN'
                )
                result['confidence'] = malware_prob

                # Flag for quantum analysis if low confidence
                if abs(malware_prob - 0.5) < (1.0 - CONFIDENCE_THRESHOLD):
                    result['quantum_recommended'] = True
            except Exception as e:
                logger.error(f"File prediction failed: {e}")
        elif features is None:
            result['note'] = 'Could not extract features'
        else:
            result['note'] = 'No EMBER model loaded'

        # VirusTotal lookup
        if not self.offline and VT_API_KEY and hashes.get('sha256'):
            vt = self._check_virustotal(hashes['sha256'])
            if vt:
                result['virustotal'] = vt

        return result

    def scan_directory(self, dir_path: str, recursive: bool = True) -> dict:
        """Scan all files in a directory."""
        path = validate_directory_path(dir_path)

        files = list(path.rglob('*') if recursive else path.glob('*'))
        files = [f for f in files if f.is_file()]

        results = {
            'type': 'directory',
            'target': str(path),
            'timestamp': datetime.now().isoformat(),
            'total_files': len(files),
            'files': [],
            'summary': {'malicious': 0, 'benign': 0, 'unknown': 0},
        }

        for f in files:
            try:
                r = self.scan_file(str(f))
                results['files'].append(r)
                pred = r.get('prediction', 'UNKNOWN')
                if pred == 'MALICIOUS':
                    results['summary']['malicious'] += 1
                elif pred == 'BENIGN':
                    results['summary']['benign'] += 1
                else:
                    results['summary']['unknown'] += 1
            except (ValidationError, Exception) as e:
                logger.warning(f"Skipping {f}: {e}")

        return results

    def _check_virustotal(self, file_hash: str) -> dict:
        """Check a file hash against VirusTotal."""
        import requests

        try:
            url = f'https://www.virustotal.com/api/v3/files/{file_hash}'
            headers = {'x-apikey': VT_API_KEY}
            resp = requests.get(url, headers=headers, timeout=10, verify=True)

            if resp.status_code == 200:
                stats = (resp.json()
                         .get('data', {})
                         .get('attributes', {})
                         .get('last_analysis_stats', {}))
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'total': sum(stats.values()),
                }
            elif resp.status_code == 404:
                return {'status': 'not_found'}
            else:
                return {'status': 'error', 'code': resp.status_code}
        except Exception as e:
            logger.warning(f"VT lookup failed: {e}")
            return None


# ─────────────────────────────────────────────────────
# CLI Output Formatting
# ─────────────────────────────────────────────────────

def print_banner():
    print(f"\n{Colors.BOLD}{Colors.HEADER}"
          f"╔═══════════════════════════════════════════════════════════╗\n"
          f"║   Quantum-Enhanced Threat Intelligence Scanner v2.0      ║\n"
          f"╚═══════════════════════════════════════════════════════════╝"
          f"{Colors.ENDC}\n")


def print_result(result: dict, as_json: bool = False):
    """Pretty-print a scan result."""
    if as_json:
        print(json.dumps(result, indent=2, default=str))
        return

    scan_type = result.get('type', 'unknown')
    target = result.get('target', '?')
    prediction = result.get('prediction', 'UNKNOWN')
    confidence = result.get('confidence', 0.0)

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}SCAN RESULT — {scan_type.upper()}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"  Target:     {target}")

    if 'hashes' in result:
        h = result['hashes']
        print(f"  MD5:        {h.get('md5', 'N/A')}")
        print(f"  SHA256:     {h.get('sha256', 'N/A')}")

    if 'features' in result and isinstance(result['features'], dict):
        print(f"\n  {Colors.OKCYAN}Features:{Colors.ENDC}")
        for k, v in result['features'].items():
            print(f"    {k}: {v:.4f}" if isinstance(v, float) else f"    {k}: {v}")

    # Verdict
    if prediction == 'MALICIOUS':
        color, icon = Colors.FAIL, '🚨'
    elif prediction == 'BENIGN':
        color, icon = Colors.OKGREEN, '✅'
    else:
        color, icon = Colors.WARNING, '⚠'

    print(f"\n  {color}{Colors.BOLD}{icon} Verdict: {prediction}  "
          f"(confidence: {confidence:.1%}){Colors.ENDC}")

    if result.get('virustotal'):
        vt = result['virustotal']
        if 'malicious' in vt:
            print(f"  VirusTotal: {vt['malicious']}/{vt.get('total', '?')} detections")

    if result.get('quantum_recommended'):
        print(f"  {Colors.WARNING}⚡ Quantum analysis recommended "
              f"(low confidence){Colors.ENDC}")

    if result.get('note'):
        print(f"  {Colors.OKCYAN}ℹ {result['note']}{Colors.ENDC}")

    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_directory_result(result: dict, as_json: bool = False):
    """Pretty-print a directory scan result."""
    if as_json:
        print(json.dumps(result, indent=2, default=str))
        return

    s = result.get('summary', {})
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}DIRECTORY SCAN — {result['target']}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"  Total files: {result['total_files']}")
    print(f"  {Colors.FAIL}Malicious: {s.get('malicious', 0)}{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}Benign:    {s.get('benign', 0)}{Colors.ENDC}")
    print(f"  {Colors.WARNING}Unknown:   {s.get('unknown', 0)}{Colors.ENDC}")

    # Show malicious files
    mal_files = [f for f in result.get('files', [])
                 if f.get('prediction') == 'MALICIOUS']
    if mal_files:
        print(f"\n  {Colors.FAIL}Threats found:{Colors.ENDC}")
        for f in mal_files:
            print(f"    🚨 {f['target']} ({f['confidence']:.1%})")

    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


# ─────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog='qeti',
        description='Quantum-Enhanced Threat Intelligence Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py domain example.com
  python cli.py domain suspicious-abc123xyz.com
  python cli.py file malware.exe
  python cli.py dir ./samples --recursive
  python cli.py file malware.exe --json
  python cli.py domain evil.com --offline
        """,
    )

    subparsers = parser.add_subparsers(dest='command', help='Scan commands')

    # ── domain ──
    dp = subparsers.add_parser('domain', help='Scan a domain for DGA indicators')
    dp.add_argument('target', type=str, help='Domain name or URL to scan')
    dp.add_argument('--json', action='store_true', help='Output as JSON')
    dp.add_argument('--offline', action='store_true', help='Skip API lookups')

    # ── file ──
    fp = subparsers.add_parser('file', help='Scan a file for malware')
    fp.add_argument('target', type=str, help='Path to file to scan')
    fp.add_argument('--json', action='store_true', help='Output as JSON')
    fp.add_argument('--offline', action='store_true', help='Skip API lookups')

    # ── directory ──
    dirp = subparsers.add_parser('dir', help='Scan a directory for malware')
    dirp.add_argument('target', type=str, help='Path to directory to scan')
    dirp.add_argument('--recursive', '-r', action='store_true', default=True,
                      help='Scan subdirectories (default: True)')
    dirp.add_argument('--json', action='store_true', help='Output as JSON')
    dirp.add_argument('--offline', action='store_true', help='Skip API lookups')

    # ── batch-domains ──
    bp = subparsers.add_parser('batch-domains',
                               help='Scan multiple domains from a file')
    bp.add_argument('target', type=str, help='Path to file with domains')
    bp.add_argument('--json', action='store_true', help='Output as JSON')
    bp.add_argument('--offline', action='store_true', help='Skip API lookups')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    print_banner()

    offline = getattr(args, 'offline', False)
    as_json = getattr(args, 'json', False)

    if offline:
        print(f"{Colors.WARNING}⚙ Running in OFFLINE mode{Colors.ENDC}\n")

    try:
        engine = ThreatEngine(offline=offline)

        if args.command == 'domain':
            result = engine.scan_domain(args.target)
            print_result(result, as_json)

        elif args.command == 'file':
            result = engine.scan_file(args.target)
            print_result(result, as_json)

        elif args.command == 'dir':
            result = engine.scan_directory(
                args.target, recursive=args.recursive
            )
            print_directory_result(result, as_json)

        elif args.command == 'batch-domains':
            with open(args.target, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(domains)} domains\n")
            for domain in domains:
                try:
                    result = engine.scan_domain(domain)
                    print_result(result, as_json)
                except ValidationError as e:
                    logger.warning(f"Skipping {domain}: {e}")

    except ValidationError as e:
        print(f"\n{Colors.FAIL}✗ Validation error: {e}{Colors.ENDC}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠ Scan interrupted{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"\n{Colors.FAIL}✗ Fatal error: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == '__main__':
    main()
