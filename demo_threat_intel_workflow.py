#!/usr/bin/env python3
"""
Complete Threat Intelligence Workflow
Demonstrates hash lookup, ML analysis, and threat correlation
"""

import json
from pathlib import Path
from scanner.threat_scanner_v2 import FileAnalyzer, DomainAnalyzer
from threat_intelligence import ThreatIntelligence

def demo_hash_lookup():
    """Demonstrate hash lookup and threat correlation"""
    print("\n" + "="*70)
    print("THREAT INTELLIGENCE WORKFLOW DEMO")
    print("="*70)
    
    # Step 1: Initialize components
    print("\n[1] INITIALIZING COMPONENTS")
    file_analyzer = FileAnalyzer()
    ti = ThreatIntelligence()
    
    # Step 2: Create sample files for demonstration
    print("\n[2] CREATING TEST FILES")
    test_files = []
    
    # Create a benign test file
    benign_file = Path('test_benign.bin')
    benign_file.write_bytes(b'\x00' * 1000)
    test_files.append(('test_benign.bin', 'BENIGN'))
    print(f"  Created: {benign_file}")
    
    # Create a suspicious test file
    suspicious_file = Path('test_suspicious.bin')
    suspicious_file.write_bytes(b'\x90' * 1000)  # NOP sled
    test_files.append(('test_suspicious.bin', 'SUSPICIOUS'))
    print(f"  Created: {suspicious_file}")
    
    # Step 3: Scan files
    print("\n[3] SCANNING FILES")
    for file_path, expected_type in test_files:
        print(f"\n  Scanning: {file_path}")
        result = file_analyzer.scan_file(file_path)
        
        file_hashes = result.get('hashes', {})
        print(f"    MD5:    {file_hashes.get('md5', 'N/A')}")
        print(f"    SHA1:   {file_hashes.get('sha1', 'N/A')}")
        print(f"    SHA256: {file_hashes.get('sha256', 'N/A')}")
        print(f"    ML Verdict: {result.get('prediction', 'UNKNOWN')} ({result.get('confidence', 0):.1%})")
        
        # Look up in threat intelligence
        if file_hashes.get('sha256'):
            intel = result.get('threat_intel', {})
            local_match = intel.get('sources', {}).get('database', {}).get('status') == 'found'
            print(f"    Threat Database Match: {'FOUND' if local_match else 'NOT FOUND'}")
            
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"    Final Verdict: {analysis['final_verdict']} ({analysis['final_confidence']:.1%})")
                print(f"    Reasoning: {analysis['reasoning']}")
    
    # Step 4: Hash database status
    print("\n[4] LOCAL MALWARE HASH DATABASE")
    db_path = Path('malware_hashes.json')
    if db_path.exists():
        with open(db_path) as f:
            db = json.load(f)
        print(f"  Malware hashes in database: {len(db)}")
        for hash_val, info in db.items():
            print(f"    - {info['name']} ({hash_val[:16]}...)")
            print(f"      Type: {info['type']}, Severity: {info['severity']}")
    
    # Step 5: Demonstrate provided hashes
    print("\n[5] LOOKING UP PROVIDED HASHES")
    provided_hashes = {
        'md5': '9e60393da455f93b0ec32cf124432651',
        'sha256': '84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258'
    }
    
    for hash_type, hash_val in provided_hashes.items():
        print(f"\n  {hash_type.upper()}: {hash_val}")
        result = ti.lookup_hash(hash_val, hash_type)
        db_intel = result.get('sources', {}).get('database', {})
        
        if db_intel.get('status') == 'found':
            print(f"    STATUS: FOUND IN DATABASE")
            print(f"    Name: {db_intel.get('threat_name')}")
            print(f"    Type: {db_intel.get('threat_type')}")
            print(f"    Severity: {db_intel.get('severity')}")
        else:
            print(f"    STATUS: Not in local database")
        
        # Correlate with ML
        correlation = ti.correlate_with_ml(
            ml_prediction='MALWARE',
            ml_confidence=0.70,
            threat_intel=result
        )
        print(f"    Final Verdict: {correlation['final_verdict']}")
        print(f"    Confidence: {correlation['final_confidence']:.1%}")
        print(f"    Reasoning: {correlation['reasoning']}")
    
    # Step 6: Summary
    print("\n[6] WORKFLOW SUMMARY")
    print("""
    The threat intelligence system provides:
    
    1. HASH COMPUTATION
       - MD5, SHA1, SHA256 for every file
       - Unique file identification
    
    2. LOCAL DATABASE LOOKUP
       - Fast (<1ms) check against known malware
       - No external API calls required
    
    3. ML ANALYSIS
       - Behavioral detection of unknown malware
       - Feature extraction and prediction
    
    4. RESULT CORRELATION
       - Combines database + ML signals
       - Confidence-weighted verdict
       - Reasoning explanation
    
    5. OPTIONAL EXTERNAL INTEGRATION
       - VirusTotal API (70+ vendors)
       - MISP feeds (threat intelligence)
       - Custom threat feeds
    """)
    
    # Cleanup
    print("\n[7] CLEANUP")
    for file_path, _ in test_files:
        try:
            Path(file_path).unlink()
            print(f"  Deleted: {file_path}")
        except:
            pass
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70 + "\n")


if __name__ == '__main__':
    demo_hash_lookup()
