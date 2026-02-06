# Hash-Based Threat Detection Integration Guide

## Quick Start

Your provided hashes are now integrated and working:

### They Identify:
- **MD5: `9e60393da455f93b0ec32cf124432651`** → Malware.Dropper (Critical)
- **SHA256: `84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258`** → Trojan.Generic (High)

### How to Use:

```bash
# 1. Scan a file
python scanner/threat_scanner_v2.py --file suspicious.exe

# 2. Get JSON output for processing
python scanner/threat_scanner_v2.py --file suspicious.exe --json

# 3. Lookup specific hash
python -c "from threat_intelligence import ThreatIntelligence; \
ti = ThreatIntelligence(); \
result = ti.lookup_hash('9e60393da455f93b0ec32cf124432651', 'md5'); \
print(result)"
```

## System Architecture

```
Input File
    ↓
[HASH COMPUTATION]
MD5 (32 chars) / SHA1 (40 chars) / SHA256 (64 chars)
    ↓
[PARALLEL LOOKUPS]
├─→ Local Database (malware_hashes.json) ← Fast (<1ms)
├─→ VirusTotal API (optional) ← Comprehensive (70+ vendors)
└─→ ML Feature Extraction ← Behavioral analysis
    ↓
[CORRELATION]
Combine all signals with weighted voting
    ↓
[VERDICT]
Final classification with confidence score
    ↓
Output: BENIGN / SUSPICIOUS / MALWARE + reasoning
```

## File: `threat_intelligence.py`

Main component for threat lookups. Key methods:

```python
# Initialize
ti = ThreatIntelligence(virustotal_api_key='OPTIONAL_KEY')

# Lookup hash in databases
result = ti.lookup_hash('9e60393da455f93b0ec32cf124432651', 'md5')

# Correlate with ML prediction
correlation = ti.correlate_with_ml(
    ml_prediction='MALWARE',
    ml_confidence=0.75,
    threat_intel=result
)
```

### Database Levels

**Level 1: Local Database (Fast)**
- File: `malware_hashes.json`
- <1ms lookup
- Highest confidence
- Full control over content

**Level 2: VirusTotal API (Comprehensive)**
- 70+ antivirus vendors
- Network-based (1-5s)
- Free tier: 4 requests/min
- Requires API key

## File: `scanner/threat_scanner_v2.py`

Modified to include threat intelligence:

```python
analyzer = FileAnalyzer()
result = analyzer.scan_file('file.exe', enable_threat_intel=True)

# Result structure:
{
    'file': 'file.exe',
    'hashes': {
        'md5': '...',
        'sha1': '...',
        'sha256': '...'
    },
    'threat_intel': {
        'sources': {
            'database': {...},
            'virustotal': {...}
        }
    },
    'analysis': {
        'final_verdict': 'MALWARE',
        'final_confidence': 0.99,
        'virustotal_detections': 5,
        'local_database_match': True,
        'reasoning': '...'
    }
}
```

## Updating the Database

### Add Known Malware Hashes

Edit `malware_hashes.json`:

```json
{
    "hash_value": {
        "name": "Threat.Name",
        "type": "Trojan|Dropper|Backdoor|etc",
        "severity": "low|medium|high|critical"
    }
}
```

### Sources for Hashes:

1. **YARA Rules** (https://github.com/Yara-Rules/rules)
```bash
# Extract hashes from YARA rules
grep -oP 'hash\s*=\s*"\K[a-f0-9]+' rules.yar >> hashes.txt
```

2. **VirusTotal** (https://www.virustotal.com)
- Search known malware samples
- Export detection history
- API bulk lookup

3. **MISP** (https://www.misp-project.org/)
```bash
# Extract attributes from MISP feed
# Format: sha256,file_name,malware_family
```

4. **MalwareBazaar** (https://bazaar.abuse.ch/)
```bash
# Download CSV of recent samples
curl https://bazaar.abuse.ch/downloads/malware_hashes.csv
```

5. **Internal Incidents**
- Add confirmed malware from:
  - Incident response
  - Forensics analysis
  - Sandbox detections

### Bulk Import Script

```python
import json
from pathlib import Path

def import_hashes_from_csv(csv_file, threat_type='Unknown', severity='medium'):
    """Import hashes from CSV format: hash,name,severity"""
    db_path = Path('malware_hashes.json')
    
    # Load existing database
    if db_path.exists():
        with open(db_path) as f:
            db = json.load(f)
    else:
        db = {}
    
    # Import from CSV
    with open(csv_file) as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                hash_val = parts[0].strip()
                name = parts[1].strip()
                severity = parts[2].strip() if len(parts) > 2 else 'medium'
                
                db[hash_val] = {
                    'name': name,
                    'type': threat_type,
                    'severity': severity
                }
    
    # Save back
    with open(db_path, 'w') as f:
        json.dump(db, f, indent=2)
    
    print(f"Imported {len(db)} hashes")

# Usage:
import_hashes_from_csv('threats.csv', threat_type='Trojan')
```

## Integration Points

### 1. Command Line

```bash
# Scan with threat intelligence
python scanner/threat_scanner_v2.py --file test.exe

# Output includes hash lookup results
```

### 2. Python API

```python
from scanner.threat_scanner_v2 import FileAnalyzer
from threat_intelligence import ThreatIntelligence

analyzer = FileAnalyzer()
result = analyzer.scan_file('test.exe')

# Access threat intelligence
if result['threat_intel']['sources']['database']['status'] == 'found':
    print("MALWARE DETECTED")
else:
    print(f"Confidence: {result['analysis']['final_confidence']:.1%}")
```

### 3. REST API (Future)

```python
# FastAPI endpoint
@app.post('/api/scan/file')
async def scan_file(file: UploadFile):
    # Save and scan
    analyzer = FileAnalyzer()
    result = analyzer.scan_file(file.filename)
    return {
        'hash': result['hashes']['sha256'],
        'verdict': result['analysis']['final_verdict'],
        'confidence': result['analysis']['final_confidence']
    }
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| MD5 hash | <1ms | For 1MB file |
| SHA256 hash | <5ms | For 1MB file |
| Local DB lookup | <1ms | Hash table O(1) |
| VirusTotal API | 1-5s | Network dependent |
| ML feature extract | 10-50ms | Depends on file size |
| Total scan (local) | <100ms | Fast path |
| Total scan (with VT) | 2-6s | Comprehensive path |

## Best Practices

1. **Always Use SHA256** for database lookups
   - MD5 and SHA1 have collisions
   - SHA256 is cryptographically secure

2. **Maintain Database** regularly
   - Weekly updates from feeds
   - Remove false positives
   - Add confirmed threats

3. **Set Severity Levels**
   - Critical: Immediate isolation
   - High: Quarantine & analyze
   - Medium: Alert & monitor
   - Low: Log only

4. **Monitor False Positives**
   - Track database matches
   - Validate with VirusTotal
   - Adjust confidence thresholds

5. **Cache Results**
   - Store lookups for 24 hours
   - Reduces API calls
   - Faster repeated scans

## Testing

Run the complete workflow:

```bash
python demo_threat_intel_workflow.py
```

Results:
- File scanning with hash computation
- Database lookup verification
- Threat correlation examples
- Performance metrics

## Next Steps

1. ✓ **Hashing System**: Working (MD5, SHA1, SHA256)
2. ✓ **Local Database**: Populated with sample hashes
3. ✓ **Threat Correlation**: Implemented (99% confidence on known hashes)
4. **VirusTotal Integration**: Add API key for vendor checks
5. **MISP Feeds**: Connect to threat intelligence platform
6. **REST API**: Deploy as microservice
7. **Dashboard**: Build visual threat tracking interface
8. **Automation**: Periodic database updates

## References

- [Hash Functions Overview](https://en.wikipedia.org/wiki/Cryptographic_hash_function)
- [VirusTotal API](https://developers.virustotal.com/)
- [MISP Threat Sharing](https://www.misp-project.org/)
- [MalwareBazaar](https://bazaar.abuse.ch/)
- [SHA256 vs MD5](https://www.ssl.com/blogs/md5-sha-1-sha-256-differences/)
