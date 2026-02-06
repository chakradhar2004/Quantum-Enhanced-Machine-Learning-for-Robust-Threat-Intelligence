# Quick Start Guide - Quantum-Enhanced Threat Scanner

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Verify Installation
```bash
python scanner/threat_scanner.py --help
```

### Step 3: Run Your First Scan

#### Scan a Domain (No API key needed)
```bash
python scanner/threat_scanner.py --domain google.com
```

#### Scan a File (Offline Mode)
```bash
python scanner/threat_scanner.py --file path/to/file.exe --offline
```

## 📝 Common Use Cases

### 1. Security Analyst - Quick Domain Check
```bash
# Check if a domain is a potential DGA
python scanner/threat_scanner.py --domain suspicious-random-chars.xyz
```

### 2. Malware Researcher - Deep File Analysis
```bash
# Full analysis with VirusTotal
set VT_API_KEY=your_key_here
python scanner/threat_scanner.py --file malware_sample.exe
```

### 3. SOC Team - Batch Domain Monitoring
```bash
# Create domains.txt with one domain per line
python scanner/threat_scanner.py --domain-file domains.txt
```

### 4. Incident Response - Fast Offline Analysis
```bash
# No internet? No problem!
python scanner/threat_scanner.py --file suspicious.exe --offline
```

## 🎯 Understanding Output

### Confidence Levels
- **80%+**: High confidence - Trust the result
- **60-80%**: Medium confidence - Result is likely accurate
- **<60%**: Low confidence - Quantum analysis recommended

### Threat Levels
- **✅ BENIGN**: No threat detected
- **⚠ SUSPICIOUS**: Low confidence or conflicting signals
- **❌ MALICIOUS**: Threat detected with high confidence
- **🚨 THREAT DETECTED**: Confirmed malicious activity

### Quantum Analysis Trigger
Automatically triggered when:
- ML confidence < 60%
- Unclear or borderline cases
- Complex or obfuscated samples

## 🔧 Configuration

### Set VirusTotal API Key (Optional but Recommended)
```bash
# Windows
set VT_API_KEY=your_virustotal_api_key

# Linux/Mac
export VT_API_KEY=your_virustotal_api_key
```

### Customize Settings
Edit `scanner/config/config.py`:
```python
CONFIDENCE_THRESHOLD = 0.60  # Quantum trigger threshold
MALWARE_THRESHOLD = 0.50     # Malware classification threshold
MAX_FILE_SIZE_MB = 100       # Maximum file size to scan
```

## 📊 View Scan History

### Show Statistics
```bash
python scanner/threat_scanner.py --stats
```

### View Detailed Logs
- **JSON**: `scanner/logs/scan_history.json`
- **CSV**: `scanner/logs/scan_history.csv`

Open in Excel or any CSV viewer for analysis.

## 🐛 Troubleshooting

### "Models not found"
**Solution**: Ensure you have the trained models:
```
models/domain_rf_model.pkl
models/ember_rf_model.pkl
```

### "pefile not available"
**Solution**:
```bash
pip install pefile lief
```

### VirusTotal not working
**Solutions**:
1. Check API key is correct
2. Verify internet connection
3. Use `--offline` flag to skip VT lookup

### Slow scans
**Solutions**:
- Use `--no-quantum` to skip quantum analysis
- Increase `MAX_FILE_SIZE_MB` threshold
- Scan smaller files first

## 💡 Pro Tips

1. **Use Offline Mode** when internet is unavailable or for privacy
2. **Set VT API Key** as environment variable to avoid typing it each time
3. **Batch Scan** multiple domains to save time
4. **Check Logs** regularly to track detection patterns
5. **Enable Quantum** for borderline cases - it's the secret weapon!

## 🎓 What's Happening Under the Hood?

1. **File Scanner**:
   - Calculates cryptographic hashes
   - Queries VirusTotal (if online)
   - Extracts 37 PE file features
   - ML classifier predicts malware probability

2. **Domain Scanner**:
   - Extracts 5 linguistic features
   - Detects DGA patterns
   - ML classifier identifies suspicious domains

3. **Quantum Analyzer** (Low Confidence Cases):
   - Applies quantum kernel methods
   - Detects subtle anomalies
   - Provides enhanced decision support

## 📚 Next Steps

- Read full documentation: `SCANNER_README.md`
- Run tests: `python tests/test_scanner.py`
- Explore logs: `scanner/logs/`
- Build executable: `pyinstaller threat_scanner.spec`

## 🆘 Need Help?

Check the full README for:
- Detailed API documentation
- Advanced configuration options
- Deployment guides (Docker, PyInstaller)
- Troubleshooting section

---

**Happy Scanning! 🔍🛡️**
