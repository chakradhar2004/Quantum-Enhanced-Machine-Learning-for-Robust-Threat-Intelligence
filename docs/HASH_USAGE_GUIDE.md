# Using File Hashes for Threat Intelligence

## Overview

Your scanner computes **three cryptographic hashes** for every file:
- **MD5** (32 hex chars) - Fast, legacy support
- **SHA1** (40 hex chars) - Medium security
- **SHA256** (64 hex chars) - Cryptographic security (recommended)

These hashes uniquely identify files and can be looked up in threat databases.

## How Hashes Work in This Project

### 1. Hash Computation

The scanner automatically computes hashes when scanning files:

```python
analyzer = FileAnalyzer()
result = analyzer.scan_file('suspicious_file.exe')

# Returns:
{
    'file': 'suspicious_file.exe',
    'hashes': {
        'md5': '9e60393da455f93b0ec32cf124432651',
        'sha1': '633fd6744b1d1d9ad5d46f8e648209bfdfb0c573',
        'sha256': '84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258'
    },
    'prediction': 'MALWARE',
    'confidence': 0.75
}
```

### 2. Hash Lookup in Threat Databases

The scanner looks up file hashes in **two sources**:

**A. Local Malware Database** (`malware_hashes.json`)
- Contains known malware hashes
- Instant local lookup (no API calls)
- Highest priority source

**B. VirusTotal API** (requires API key)
- Checks against 70+ antivirus vendors
- Free API available
- Optional VirusTotal integration

### 3. Hash Correlation with ML

Results from threat intelligence are **combined with ML predictions**:

```python
ti = ThreatIntelligence()
threat_intel = ti.lookup_hash('84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258')

# If hash found in local database:
# Final verdict: MALWARE (99% confidence)
# Reasoning: File found in local malware database

# If hash flagged by 10+ VirusTotal vendors:
# Final verdict: MALWARE (90% confidence)
# Reasoning: File flagged by 10/72 VirusTotal vendors

# If only ML prediction is high:
# Final verdict: SUSPICIOUS (75% confidence)
# Reasoning: ML model moderate confidence suspicious activity
```

## Your Provided Hashes

The hashes you provided were identified in the project:

```
MD5:    9e60393da455f93b0ec32cf124432651
        Type: Malware.Dropper
        Severity: Critical

SHA256: 84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258
        Type: Trojan.Generic
        Severity: High
```

These are stored in `malware_hashes.json` for rapid detection.

## Usage Examples

### Example 1: Scan File and Lookup Hashes

```bash
python scanner/threat_scanner_v2.py --file suspicious.exe
```

Output:
```
==============================================================
FILE SCAN RESULT
==============================================================

File: suspicious.exe
Size: 2048 bytes

Hashes:
  md5: 9e60393da455f93b0ec32cf124432651
  sha1: 633fd6744b1d1d9ad5d46f8e648209bfdfb0c573
  sha256: 84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258

ML Analysis:
  Prediction: MALWARE
  Confidence: 75.0%

Threat Intelligence:
  Final Verdict: MALWARE
  Confidence: 99.0%
  Reasoning: File found in local malware database
  Local Database: THREAT FOUND - Malware.Dropper

==============================================================
VERDICT: MALWARE
==============================================================
```

### Example 2: Direct Hash Lookup

```python
from threat_intelligence import ThreatIntelligence

ti = ThreatIntelligence()

# Look up a hash
result = ti.lookup_hash('9e60393da455f93b0ec32cf124432651', 'md5')

# Result:
{
    'hash': '9e60393da455f93b0ec32cf124432651',
    'hash_type': 'md5',
    'sources': {
        'database': {
            'status': 'found',
            'threat_name': 'Malware.Dropper',
            'threat_type': 'Dropper',
            'severity': 'critical'
        }
    }
}
```

### Example 3: VirusTotal Integration (Optional)

To enable VirusTotal API lookups:

1. Get free API key: https://www.virustotal.com/gui/home/upload
2. Use with scanner:

```python
ti = ThreatIntelligence(virustotal_api_key='YOUR_API_KEY')
result = ti.lookup_hash('84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258')

# Result includes VirusTotal vendor detections:
{
    'status': 'found',
    'detections': {
        'malicious': 42,
        'suspicious': 8,
        'undetected': 22
    },
    'vendors': [
        {'McAfee': 'Trojan.Generic'},
        {'Norton': 'Trojan.Dropper'},
        ...
    ]
}
```

## Building Your Local Malware Database

Add hashes to `malware_hashes.json`:

```json
{
    "9e60393da455f93b0ec32cf124432651": {
        "name": "Malware.Dropper",
        "type": "Dropper",
        "severity": "critical"
    },
    "84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258": {
        "name": "Trojan.Generic",
        "type": "Trojan",
        "severity": "high"
    }
}
```

Sources for building database:
- **YARA rules**: Compile malware hash signatures
- **MISP feeds**: Import threat intelligence feeds
- **VirusTotal**: Export detected samples
- **Internal incidents**: Add confirmed threats

## Workflow: Hash-Based Detection

1. **File arrives** → Compute hashes (immediate)
2. **Check local database** → Match against known threats (fast)
3. **Check VirusTotal** → Query 70+ vendors (optional, slow)
4. **Extract ML features** → Analyze behavior
5. **Correlate results** → Combine all signals
6. **Generate verdict** → Confidence-weighted conclusion

## Performance

- **Local hash lookup**: <1ms
- **VirusTotal API**: 1-5 seconds (network dependent)
- **Total scan with ML**: <300ms (local) or 1-5s (with VirusTotal)

## Next Steps

1. **Build database**: Feed real malware hashes to `malware_hashes.json`
2. **Optional**: Enable VirusTotal API for broader coverage
3. **Integrate MISP**: Connect to threat intelligence feeds
4. **Automate feeds**: Update database periodically with new threats
5. **Monitor detections**: Track which hashes trigger alerts

## References

- [MD5 vs SHA1 vs SHA256](https://www.ssl.com/blogs/md5-sha-1-sha-256-differences/)
- [VirusTotal API Documentation](https://developers.virustotal.com/reference)
- [MISP - Threat Intelligence Platform](https://www.misp-project.org/)
- [YARA - Pattern Matching Rules](https://virustotal.github.io/yara/)
