# Usage Examples - Quantum-Enhanced Threat Scanner

This file contains practical examples for using the threat scanner in various scenarios.

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [File Scanning](#file-scanning)
3. [Domain Scanning](#domain-scanning)
4. [Advanced Features](#advanced-features)
5. [Integration Examples](#integration-examples)

---

## Basic Usage

### Check Installation
```bash
python scanner/threat_scanner.py --help
```

### Show Statistics
```bash
python scanner/threat_scanner.py --stats
```

---

## File Scanning

### Scan a Single File (Offline)
```bash
python scanner/threat_scanner.py --file C:\suspicious\malware.exe --offline
```

### Scan with VirusTotal Integration
```bash
# Method 1: Set environment variable
set VT_API_KEY=your_virustotal_api_key_here
python scanner/threat_scanner.py --file malware.exe

# Method 2: Pass API key directly
python scanner/threat_scanner.py --file malware.exe --vt-key YOUR_API_KEY
```

### Scan Without Quantum Analysis
```bash
# Faster scan, skip quantum analysis even for low confidence
python scanner/threat_scanner.py --file sample.exe --no-quantum
```

### Full Analysis Pipeline
```bash
# Complete analysis with all features enabled
python scanner/threat_scanner.py --file suspicious.exe
```

**What happens:**
1. Computes MD5, SHA1, SHA256 hashes
2. Queries VirusTotal (if online and API key provided)
3. Extracts 37 static PE features using pefile/lief
4. Random Forest classifier predicts malware probability
5. If confidence < 60%, triggers quantum analysis automatically
6. Logs results to JSON and CSV
7. Displays color-coded verdict

---

## Domain Scanning

### Scan a Single Domain
```bash
python scanner/threat_scanner.py --domain suspicious-domain.xyz
```

### Scan a Full URL
```bash
python scanner/threat_scanner.py --domain https://example.com/page
```

### Batch Scan Multiple Domains
```bash
# Create a file with domains (one per line)
python scanner/threat_scanner.py --domain-file sample_domains.txt
```

**sample_domains.txt format:**
```
google.com
suspicious123abc.net
randomchars.xyz
facebook.com
```

### Scan DGA-like Domains
```bash
# These will likely trigger high malicious scores
python scanner/threat_scanner.py --domain xj3k9dkf2jdk.com
python scanner/threat_scanner.py --domain qwerty123abc.net
```

---

## Advanced Features

### Offline Mode (No API Calls)
```bash
# Useful when:
# - No internet connection
# - Privacy concerns
# - Quick local analysis needed
python scanner/threat_scanner.py --file malware.exe --offline
python scanner/threat_scanner.py --domain test.com --offline
```

### Force Quantum Analysis
```python
# Python script to always use quantum analysis
from scanner.threat_scanner import ThreatScanner

scanner = ThreatScanner(offline_mode=True)
scanner.scan_file('sample.exe', auto_quantum=True)
```

### Custom Configuration
Edit `scanner/config/config.py`:
```python
# Lower threshold = more quantum analyses
CONFIDENCE_THRESHOLD = 0.70

# Higher threshold = stricter malware detection
MALWARE_THRESHOLD = 0.60

# Increase max file size
MAX_FILE_SIZE_MB = 200
```

---

## Integration Examples

### Example 1: Python Script Integration
```python
#!/usr/bin/env python3
"""
Example: Integrate scanner into your Python script
"""
import sys
from pathlib import Path

# Add scanner to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner.modules.domain_scanner import DomainScanner
from scanner.modules.file_scanner import FileScanner
from scanner.core.logger import get_logger

def scan_multiple_files(file_list):
    """Scan multiple files and generate report"""
    scanner = FileScanner(offline_mode=True)
    results = []
    
    for file_path in file_list:
        print(f"Scanning {file_path}...")
        result = scanner.scan_file(file_path)
        results.append(result)
    
    # Generate summary
    malicious_count = sum(1 for r in results if r.get('ml_prediction') == 'MALICIOUS')
    print(f"\nSummary: {malicious_count}/{len(results)} files flagged as malicious")
    
    return results

if __name__ == '__main__':
    files = ['sample1.exe', 'sample2.exe', 'sample3.dll']
    scan_multiple_files(files)
```

### Example 2: Automated Security Pipeline
```python
#!/usr/bin/env python3
"""
Example: Automated security scanning pipeline
"""
from pathlib import Path
from scanner.threat_scanner import ThreatScanner
import json

def security_pipeline(scan_dir, vt_api_key=None):
    """
    Scan all executables in a directory
    """
    scanner = ThreatScanner(vt_api_key=vt_api_key, offline_mode=not vt_api_key)
    
    # Find all executables
    scan_dir = Path(scan_dir)
    executables = list(scan_dir.glob('**/*.exe')) + list(scan_dir.glob('**/*.dll'))
    
    print(f"Found {len(executables)} files to scan")
    
    threats_detected = []
    
    for exe in executables:
        print(f"\n{'='*60}")
        print(f"Scanning: {exe.name}")
        print(f"{'='*60}")
        
        results = scanner.file_scanner.scan_file(str(exe))
        
        if results.get('ml_prediction') == 'MALICIOUS':
            threats_detected.append({
                'file': str(exe),
                'confidence': results.get('ml_confidence'),
                'hashes': results.get('hashes')
            })
    
    # Save threat report
    if threats_detected:
        with open('threat_report.json', 'w') as f:
            json.dump(threats_detected, f, indent=2)
        print(f"\n⚠ {len(threats_detected)} threats detected!")
        print("Report saved to: threat_report.json")
    else:
        print("\n✓ No threats detected")
    
    return threats_detected

if __name__ == '__main__':
    import sys
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    security_pipeline(directory)
```

### Example 3: Domain Monitoring
```python
#!/usr/bin/env python3
"""
Example: Monitor domains for DGA activity
"""
from scanner.modules.domain_scanner import DomainScanner
import pandas as pd
from datetime import datetime

def monitor_domains(domain_file, output_csv='domain_report.csv'):
    """
    Monitor domains and generate CSV report
    """
    scanner = DomainScanner(offline_mode=True)
    
    # Read domains
    with open(domain_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]
    
    results = []
    
    for domain in domains:
        print(f"Checking {domain}...")
        scan_result = scanner.scan_domain(domain)
        
        results.append({
            'timestamp': datetime.now().isoformat(),
            'domain': domain,
            'prediction': scan_result.get('ml_prediction'),
            'confidence': scan_result.get('ml_confidence'),
            'length': scan_result.get('features', {}).get('length'),
            'entropy': scan_result.get('features', {}).get('entropy')
        })
    
    # Save to CSV
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    
    print(f"\nReport saved to: {output_csv}")
    
    # Summary
    malicious = df[df['prediction'] == 'MALICIOUS']
    print(f"Malicious domains: {len(malicious)}/{len(df)}")
    
    return df

if __name__ == '__main__':
    monitor_domains('sample_domains.txt')
```

### Example 4: REST API Wrapper
```python
#!/usr/bin/env python3
"""
Example: Create a simple REST API for the scanner
"""
from flask import Flask, request, jsonify
from scanner.threat_scanner import ThreatScanner
import tempfile
import os

app = Flask(__name__)
scanner = ThreatScanner(offline_mode=True)

@app.route('/scan/domain', methods=['POST'])
def scan_domain_api():
    """Scan a domain via API"""
    data = request.get_json()
    domain = data.get('domain')
    
    if not domain:
        return jsonify({'error': 'Domain required'}), 400
    
    results = scanner.domain_scanner.scan_domain(domain)
    
    return jsonify({
        'domain': domain,
        'prediction': results.get('ml_prediction'),
        'confidence': results.get('ml_confidence'),
        'features': results.get('features')
    })

@app.route('/scan/file', methods=['POST'])
def scan_file_api():
    """Scan a file via API"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        results = scanner.file_scanner.scan_file(tmp_path)
        
        return jsonify({
            'filename': file.filename,
            'prediction': results.get('ml_prediction'),
            'confidence': results.get('ml_confidence'),
            'hashes': results.get('hashes')
        })
    finally:
        os.unlink(tmp_path)

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get scan statistics"""
    stats = scanner.logger.get_statistics()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# Usage:
# curl -X POST http://localhost:5000/scan/domain -H "Content-Type: application/json" -d '{"domain":"google.com"}'
# curl -X POST http://localhost:5000/scan/file -F "file=@malware.exe"
# curl http://localhost:5000/stats
```

---

## Batch Processing Examples

### Scan All Files in Directory
```bash
# Windows
for %f in (C:\samples\*.exe) do python scanner/threat_scanner.py --file "%f"

# Linux/Mac
for file in /path/to/samples/*.exe; do
    python scanner/threat_scanner.py --file "$file"
done
```

### PowerShell Script
```powershell
# scan_directory.ps1
$files = Get-ChildItem -Path "C:\samples" -Filter "*.exe" -Recurse

foreach ($file in $files) {
    Write-Host "Scanning: $($file.FullName)"
    python scanner/threat_scanner.py --file $file.FullName --offline
}
```

---

## Reading Scan Logs

### View Recent Scans (Python)
```python
from scanner.core.logger import get_logger

logger = get_logger()

# Get last 10 scans
recent = logger.get_scan_history(limit=10)

for scan in recent:
    print(f"{scan['timestamp']}: {scan['target']} -> {scan['result']}")
```

### Analyze Logs with Pandas
```python
import pandas as pd

# Load CSV log
df = pd.read_csv('scanner/logs/scan_history.csv')

# Filter malicious detections
malicious = df[df['result'] == 'MALICIOUS']

print(f"Total scans: {len(df)}")
print(f"Malicious detected: {len(malicious)}")
print(f"Detection rate: {len(malicious)/len(df)*100:.1f}%")

# Group by scan type
print(df.groupby('scan_type')['result'].value_counts())
```

---

## Troubleshooting Examples

### Test Model Loading
```python
from scanner.modules.file_scanner import FileScanner
from scanner.modules.domain_scanner import DomainScanner

# Test file scanner
fs = FileScanner(offline_mode=True)
print(f"File scanner model loaded: {fs.ml_model is not None}")

# Test domain scanner
ds = DomainScanner(offline_mode=True)
print(f"Domain scanner model loaded: {ds.ml_model is not None}")
```

### Verify Feature Extraction
```python
from scanner.modules.domain_scanner import DomainScanner

scanner = DomainScanner()
features, feature_dict = scanner.extract_domain_features("google.com")

print("Feature vector shape:", features.shape)
print("Feature dictionary:", feature_dict)
```

---

## Performance Optimization

### Disable Quantum for Batch Jobs
```bash
# Faster batch processing without quantum analysis
python scanner/threat_scanner.py --domain-file domains.txt --no-quantum
```

### Parallel Processing (Python)
```python
from concurrent.futures import ThreadPoolExecutor
from scanner.modules.domain_scanner import DomainScanner

def scan_domain_worker(domain):
    scanner = DomainScanner(offline_mode=True)
    return scanner.scan_domain(domain)

domains = ['google.com', 'example.com', 'test.org']

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(scan_domain_worker, domains))
```

---

**Need more examples? Check:**
- Full README: `SCANNER_README.md`
- Quick start: `QUICKSTART.md`
- Tests: `tests/test_scanner.py`
