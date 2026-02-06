#!/usr/bin/env python3
"""
Automated Directory Scan Examples
Show practical use cases for directory scanning
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

def scan_directory(directory, threat_level='all', extensions=None):
    """Run a directory scan and return results"""
    cmd = [
        'python', 'scanner/threat_scanner_v2.py',
        '--directory', directory,
        '--threat-level', threat_level,
        '--json'
    ]
    
    if extensions:
        cmd.extend(['--extensions', ','.join(extensions)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        print(f"Error: {result.stderr}")
        return None

def print_section(title):
    print(f"\n{'='*80}")
    print(title.center(80))
    print('='*80 + '\n')

def example_1_basic_scan():
    """Example 1: Basic directory scan"""
    print_section("EXAMPLE 1: Basic Directory Scan")
    
    print("Scanning test_scan_directory for all threats...")
    results = scan_directory('test_scan_directory', threat_level='all')
    
    if results:
        summary = results['summary']
        print(f"Files Scanned: {results['files_scanned']}")
        print(f"Threats Found: {results['total_files_found']}")
        print(f"\nSummary:")
        print(f"  Malware:    {summary['malware']}")
        print(f"  Suspicious: {summary['suspicious']}")
        print(f"  Benign:     {summary['benign']}")
        print(f"  Unknown:    {summary['unknown']}")

def example_2_executive_only():
    """Example 2: Scan only executable files"""
    print_section("EXAMPLE 2: Scan Only Executables")
    
    print("Scanning for .exe and .bin files only...")
    results = scan_directory(
        'test_scan_directory',
        threat_level='all',
        extensions=['exe', 'bin']
    )
    
    if results:
        print(f"Files Scanned: {results['files_scanned']}")
        print(f"Threats Found: {results['total_files_found']}")
        
        if results['files_found']:
            print(f"\nThreats:")
            for threat in results['files_found']:
                print(f"  - {threat['file']}: {threat['verdict']}")

def example_3_malware_only():
    """Example 3: Show only confirmed malware"""
    print_section("EXAMPLE 3: Show Only Confirmed Malware")
    
    print("Scanning for confirmed malware (99% confidence)...")
    results = scan_directory('test_scan_directory', threat_level='malware')
    
    if results:
        if results['total_files_found'] > 0:
            print(f"\nCONFIRMED MALWARE FOUND: {results['total_files_found']}")
            for threat in results['files_found']:
                print(f"\n  File: {threat['file']}")
                print(f"  Path: {threat['path']}")
                print(f"  Verdict: {threat['verdict']}")
                print(f"  SHA256: {threat['hashes']['sha256']}")
        else:
            print("No confirmed malware detected.")

def example_4_export_json():
    """Example 4: Export scan results to JSON file"""
    print_section("EXAMPLE 4: Export Results to JSON")
    
    print("Running scan and saving to report.json...")
    results = scan_directory('test_scan_directory', threat_level='all')
    
    if results:
        filename = f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Report saved: {filename}")
        print(f"File size: {Path(filename).stat().st_size} bytes")

def example_5_threat_analysis():
    """Example 5: Analyze threats found"""
    print_section("EXAMPLE 5: Analyze Threats")
    
    print("Scanning for suspicious files...")
    results = scan_directory('test_scan_directory', threat_level='suspicious')
    
    if results and results['files_found']:
        summary = results['summary']
        
        print(f"\nThreat Analysis:")
        print(f"  Total Files Analyzed: {summary['total']}")
        print(f"  Malware Detected: {summary['malware']}")
        print(f"  Suspicious Files: {summary['suspicious']}")
        
        print(f"\nDetailed Findings:")
        for idx, threat in enumerate(results['files_found'], 1):
            print(f"\n  [{idx}] {threat['file']}")
            print(f"      Size: {threat['size']} bytes")
            print(f"      Verdict: {threat['verdict']}")
            print(f"      Confidence: {threat['confidence']:.1%}")

def example_6_compare_scans():
    """Example 6: Compare multiple scans"""
    print_section("EXAMPLE 6: Compare Scans (Before/After)")
    
    print("This example shows how to compare scans over time.\n")
    
    # Scan 1
    results1 = scan_directory('test_scan_directory', threat_level='all')
    
    if results1:
        print("Scan 1 Results:")
        print(f"  Files: {results1['files_scanned']}")
        print(f"  Threats: {results1['total_files_found']}")
        
        # You could make changes here and scan again
        print("\n(In real scenario, make changes and scan again)")
        
        print("\nComparison:")
        print("  New threats: 0")
        print("  Removed threats: 0")
        print("  Overall status: UNCHANGED")

def main():
    print("\n" + "="*80)
    print("DIRECTORY SCANNING - PRACTICAL EXAMPLES".center(80))
    print("="*80)
    
    examples = [
        ("Basic directory scan", example_1_basic_scan),
        ("Scan only executables", example_2_executive_only),
        ("Show confirmed malware", example_3_malware_only),
        ("Export to JSON", example_4_export_json),
        ("Analyze threats", example_5_threat_analysis),
        ("Compare scans", example_6_compare_scans),
    ]
    
    for idx, (name, func) in enumerate(examples, 1):
        try:
            # Only run first 3 examples to avoid too much output
            if idx <= 3:
                func()
        except Exception as e:
            print(f"Error in {name}: {e}")
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETE".center(80))
    print("="*80)
    
    print("\n\nUSEFUL COMMANDS:")
    print("-" * 80)
    
    commands = [
        ("Scan entire directory", 
         "python scanner/threat_scanner_v2.py --directory /path"),
        
        ("Scan .exe files only", 
         "python scanner/threat_scanner_v2.py --directory /path --extensions exe,dll"),
        
        ("Find malware only", 
         "python scanner/threat_scanner_v2.py --directory /path --threat-level malware"),
        
        ("Export JSON report", 
         "python scanner/threat_scanner_v2.py --directory /path --json > report.json"),
        
        ("Quick system scan", 
         "python scanner/threat_scanner_v2.py --directory C:\\Windows --threat-level malware"),
        
        ("Get help", 
         "python scanner/threat_scanner_v2.py --help"),
    ]
    
    for desc, cmd in commands:
        print(f"\n{desc}:")
        print(f"  {cmd}")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
