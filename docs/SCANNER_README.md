# Quantum-Enhanced Threat Intelligence Scanner

A production-grade threat detection tool combining classical machine learning with quantum-enhanced analysis for advanced malware and DGA domain detection.

## 🌟 Features

- **🔍 File Scanning**: Analyze PE files (.exe, .dll, .sys) for malware signatures
- **🌐 Domain Scanning**: Detect DGA (Domain Generation Algorithm) domains
- **🔐 Hash Analysis**: Calculate MD5, SHA1, SHA256 hashes
- **🦠 VirusTotal Integration**: Query VirusTotal API for threat intelligence
- **⚛️ Quantum Analysis**: Advanced anomaly detection using quantum algorithms
- **📊 Comprehensive Logging**: JSON and CSV logging of all scans
- **🎨 Beautiful CLI**: Color-coded terminal output with clear status indicators
- **📈 Statistics Dashboard**: Track scan history and detection rates
- **🔌 Offline Mode**: Work without internet connectivity
- **⚡ Batch Processing**: Scan multiple domains from a file

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Qunatum-Enhanced_Threat_Intelligence
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

#### Scan a File
```bash
python scanner/threat_scanner.py --file suspicious.exe
```

#### Scan with VirusTotal
```bash
# Set API key as environment variable
set VT_API_KEY=your_virustotal_api_key

# Or pass directly
python scanner/threat_scanner.py --file malware.exe --vt-key YOUR_API_KEY
```

#### Scan a Domain
```bash
python scanner/threat_scanner.py --domain suspicious-domain.com
```

#### Batch Scan Domains
```bash
python scanner/threat_scanner.py --domain-file domains.txt
```

#### View Statistics
```bash
python scanner/threat_scanner.py --stats
```

#### Offline Mode
```bash
python scanner/threat_scanner.py --file sample.exe --offline
```

## 📋 Command Line Options

```
usage: threat_scanner.py [-h] [--file FILE] [--domain DOMAIN] 
                         [--domain-file DOMAIN_FILE] [--vt-key VT_KEY]
                         [--offline] [--no-quantum] [--stats]

Options:
  --file, -f FILE          File to scan
  --domain, -d DOMAIN      Domain or URL to scan
  --domain-file FILE       File containing domains (one per line)
  --vt-key KEY            VirusTotal API key
  --offline               Run without API calls
  --no-quantum            Disable automatic quantum analysis
  --stats                 Show scan statistics
```

## 🏗️ Architecture

```
scanner/
├── config/              # Configuration files
│   └── config.py       # Main configuration
├── core/               # Core functionality
│   └── logger.py       # Logging system
├── modules/            # Scanner modules
│   ├── file_scanner.py     # File/malware scanning
│   ├── domain_scanner.py   # Domain/DGA detection
│   └── quantum_analyzer.py # Quantum analysis
├── logs/               # Scan logs (auto-generated)
└── threat_scanner.py   # Main CLI application
```

## 🔬 How It Works

### File Scanning Pipeline

1. **Hash Calculation**: Compute MD5, SHA1, SHA256 hashes
2. **VirusTotal Lookup**: Check hash against VirusTotal database (if API key provided)
3. **Feature Extraction**: Extract static features from PE file using `pefile`/`lief`
4. **ML Prediction**: Random Forest classifier predicts malware probability
5. **Quantum Analysis**: If confidence < 60%, quantum anomaly detection is triggered
6. **Final Verdict**: Combined analysis produces final threat assessment

### Domain Scanning Pipeline

1. **Feature Extraction**: Extract domain characteristics (length, entropy, ratios)
2. **ML Prediction**: Random Forest classifier detects DGA domains
3. **Quantum Analysis**: Low-confidence domains analyzed with quantum methods
4. **Reputation Check**: (Extensible) Future integration with reputation APIs

### Quantum Analysis

When classical ML confidence is below 60%, the system automatically engages quantum-enhanced analysis:

- **QSVC (Quantum Support Vector Classifier)**: Uses quantum kernel for non-linear pattern detection
- **VQC (Variational Quantum Classifier)**: Leverages quantum circuits for classification
- **Simulation Mode**: Falls back to quantum-inspired simulation if quantum models unavailable

## 📊 Output Examples

### Successful Malware Detection
```
╔═══════════════════════════════════════════════════════════╗
║   Quantum-Enhanced Threat Intelligence Scanner v1.0      ║
╚═══════════════════════════════════════════════════════════╝

Scanning file: suspicious.exe

[1/4] Computing file hashes...
  MD5:    d41d8cd98f00b204e9800998ecf8427e
  SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

[2/4] Checking VirusTotal...
  Detections: 45/72
  ⚠ File flagged by 45 security engines

[3/4] Extracting PE features...
  ✓ Extracted 37 features

[4/4] Running ML analysis...
  Prediction: MALICIOUS (confidence: 94.5%)

============================================================
FINAL VERDICT
============================================================

🚨 THREAT DETECTED
```

### Benign File with Quantum Analysis
```
[4/4] Running ML analysis...
  ⚠ Low confidence (52.3%) - Quantum analysis recommended

🔬 Quantum Analysis
Engaging quantum-enhanced threat detection...

Analysis Method: QSVC
Confidence: 0.8234

✓ No significant anomalies detected
Anomaly Level: LOW

============================================================
FINAL VERDICT
============================================================

✅ BENIGN
```

## 📁 Scan Logs

All scans are automatically logged to:
- **JSON**: `scanner/logs/scan_history.json` - Detailed structured logs
- **CSV**: `scanner/logs/scan_history.csv` - Easy spreadsheet analysis

Log includes:
- Timestamp
- Scan type (file/domain)
- Target (file path/domain name)
- ML prediction and confidence
- Quantum analysis results
- VirusTotal detections
- File hashes

## 🧪 Testing

Run basic tests:
```bash
python tests/test_scanner.py
```

Test individual modules:
```bash
# Test file scanner
python -c "from scanner.modules.file_scanner import FileScanner; fs = FileScanner(); print(fs.ml_model)"

# Test domain scanner
python -c "from scanner.modules.domain_scanner import DomainScanner; ds = DomainScanner(); print('OK')"
```

## 📦 Deployment

### PyInstaller (Standalone Executable)

Create a standalone executable:
```bash
pyinstaller --onefile --name ThreatScanner scanner/threat_scanner.py
```

The executable will be in `dist/ThreatScanner.exe`

### Docker

Build and run with Docker:
```bash
docker build -t threat-scanner .
docker run -it threat-scanner --help
```

## ⚙️ Configuration

Edit `scanner/config/config.py` to customize:

- **Confidence Threshold**: Minimum confidence before quantum analysis (default: 0.60)
- **Malware Threshold**: Probability threshold for malware classification (default: 0.50)
- **Max File Size**: Maximum file size to scan in MB (default: 100)
- **Model Paths**: Locations of trained models
- **Log Paths**: Where to save scan logs

## 🔑 VirusTotal API Key

Get a free API key from [VirusTotal](https://www.virustotal.com/gui/join-us):

1. Create an account
2. Go to your profile → API Key
3. Set as environment variable:
   ```bash
   # Windows
   set VT_API_KEY=your_key_here
   
   # Linux/Mac
   export VT_API_KEY=your_key_here
   ```

## 📚 Technical Details

### Models Used

- **Domain Classifier**: Random Forest trained on 100k+ domains
- **Malware Classifier**: Random Forest trained on EMBER dataset (1M+ samples)
- **Quantum Models**: QSVC and VQC for anomaly detection

### Feature Engineering

**Domain Features (5)**:
- Length
- Shannon entropy
- Vowel ratio
- Digit ratio
- Consonant ratio

**File Features (37)**:
- Byte histograms (10)
- Byte entropy distribution (10)
- Section characteristics (5)
- Import table features (5)
- Export table features (2)
- General PE properties (5)

## 🛠️ Troubleshooting

**Q: Models not found**
```bash
# Ensure you have the trained models in the correct locations:
models/domain_rf_model.pkl
models/ember_rf_model.pkl
phase4/models/qsvc_domain_model.dill
phase4/models/vqc_domain_model.dill
```

**Q: pefile/lief not working**
```bash
pip install --upgrade pefile lief
```

**Q: VirusTotal not working**
- Check API key is valid
- Verify internet connection
- Try `--offline` mode to skip API calls

**Q: Quantum models not loading**
```bash
pip install dill qiskit pennylane
```

## 🤝 Contributing

This is an academic project. For improvements:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

Academic use only. See LICENSE file for details.

## 👥 Authors

Quantum Threat Intelligence Team

## 🙏 Acknowledgments

- EMBER dataset for malware features
- Qiskit and PennyLane for quantum computing frameworks
- VirusTotal for threat intelligence API

---

**⚠️ Disclaimer**: This tool is for educational and research purposes. Always obtain proper authorization before scanning files or systems you do not own.
