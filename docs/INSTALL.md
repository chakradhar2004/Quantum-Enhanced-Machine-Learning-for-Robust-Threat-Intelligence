# 🚀 INSTALLATION & SETUP GUIDE

Complete installation guide for the Quantum-Enhanced Threat Intelligence Scanner.

---

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Quick Install](#quick-install)
3. [Detailed Installation](#detailed-installation)
4. [First Run](#first-run)
5. [Troubleshooting](#troubleshooting)
6. [Optional Components](#optional-components)

---

## 💻 System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Storage**: 500MB for code + models
- **OS**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.14+

### Python Packages
All dependencies are listed in `requirements.txt` and will be installed automatically.

---

## ⚡ Quick Install

For users who just want to get started:

```bash
# 1. Navigate to project directory
cd Qunatum-Enhanced_Threat_Intelligence

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test installation
python scanner/threat_scanner.py --help

# 4. Run first scan
python scanner/threat_scanner.py --domain google.com --offline
```

**Done!** If this works, you're all set. If not, see [Detailed Installation](#detailed-installation).

---

## 📦 Detailed Installation

### Step 1: Clone/Download Project
```bash
# If using git:
git clone <repository-url>
cd Qunatum-Enhanced_Threat_Intelligence

# If downloaded as ZIP:
# Extract to a folder and navigate to it
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
# Create venv
python -m venv venv

# Activate
venv\Scripts\activate

# Verify
where python
# Should show path inside venv folder
```

**Linux/Mac:**
```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Verify
which python
# Should show path inside venv folder
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# This installs:
# - scikit-learn (ML models)
# - pandas, numpy (data processing)
# - tldextract (domain parsing)
# - requests (API calls)
# - pefile, lief (PE file analysis)
# - qiskit, pennylane (quantum computing)
# - dill (quantum model loading)
# - and more...
```

**Installation may take 5-10 minutes** depending on your internet connection.

### Step 4: Verify Installation

```bash
# Check Python version
python --version
# Should be 3.8 or higher

# Check if scanner loads
python scanner/threat_scanner.py --help

# Should display help message
```

---

## 🎬 First Run

### Test 1: Domain Scanning (No Setup Required)
```bash
python scanner/threat_scanner.py --domain google.com --offline
```

**Expected Output:**
```
╔═══════════════════════════════════════════════════════════╗
║   Quantum-Enhanced Threat Intelligence Scanner v1.0      ║
╚═══════════════════════════════════════════════════════════╝

Scanning domain: google.com

[1/3] Extracting domain features...
  Length: 6
  Entropy: 1.918
  ...

FINAL VERDICT
✅ BENIGN
```

### Test 2: View Statistics
```bash
python scanner/threat_scanner.py --stats
```

### Test 3: Batch Domain Scan
```bash
python scanner/threat_scanner.py --domain-file sample_domains.txt
```

### Test 4: Help & Options
```bash
python scanner/threat_scanner.py --help
```

---

## 🔧 Troubleshooting

### Issue 1: "Python not found" or "command not found"

**Solution:**
```bash
# Windows: Use full path
C:\Python310\python.exe scanner/threat_scanner.py --help

# Linux/Mac: Install Python 3
sudo apt install python3 python3-pip  # Ubuntu/Debian
brew install python3                   # macOS
```

### Issue 2: "No module named 'scanner'"

**Solution:**
```bash
# Make sure you're in the project root directory
cd Qunatum-Enhanced_Threat_Intelligence

# Verify structure
ls scanner/
# Should show: threat_scanner.py, modules/, core/, etc.
```

### Issue 3: NumPy version conflicts

**Symptoms:**
```
ImportError: A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x
```

**Solution:**
```bash
# Install compatible numpy version
pip install "numpy<2.0.0"

# Or downgrade
pip install numpy==1.24.0
```

### Issue 4: "Models not found"

**Solution:**
```bash
# Verify models exist
ls models/
# Should show: domain_rf_model.pkl, ember_rf_model.pkl

ls phase4/models/
# Should show quantum models

# If missing: You may need to train models first
# Or ensure you're using the complete project
```

### Issue 5: Sklearn/Scipy import errors

**Solution:**
```bash
# Reinstall scikit-learn and dependencies
pip install --upgrade --force-reinstall scikit-learn scipy numpy

# If still fails, create fresh virtual environment
deactivate
rm -rf venv  # or: rmdir /s venv (Windows)
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

### Issue 6: pefile/lief not working

**Solution:**
```bash
# Install individually
pip install pefile
pip install lief

# Test import
python -c "import pefile; import lief; print('OK')"
```

### Issue 7: "Permission denied" on Linux

**Solution:**
```bash
# Run with user permissions (don't use sudo with pip in venv)
# If you need to, fix venv ownership
sudo chown -R $USER:$USER venv/

# Or use --user flag
pip install --user -r requirements.txt
```

---

## 🎯 Optional Components

### VirusTotal API (Optional but Recommended)

1. **Get API Key:**
   - Go to https://www.virustotal.com/gui/join-us
   - Create free account
   - Copy API key from profile

2. **Set as Environment Variable:**
   ```bash
   # Windows (Temporary - current session)
   set VT_API_KEY=your_api_key_here

   # Windows (Permanent)
   setx VT_API_KEY "your_api_key_here"

   # Linux/Mac (Temporary)
   export VT_API_KEY=your_api_key_here

   # Linux/Mac (Permanent - add to ~/.bashrc or ~/.zshrc)
   echo 'export VT_API_KEY=your_api_key_here' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Test:**
   ```bash
   python scanner/threat_scanner.py --domain example.com
   # Should now query VirusTotal
   ```

### PE File Analysis Libraries

For scanning Windows executables:

```bash
# Install PE analyzers
pip install pefile lief

# Test
python -c "import pefile; import lief; print('PE analysis ready!')"
```

### Quantum Models (Optional)

If you want to use real quantum models:

```bash
# Install quantum packages (heavy dependencies)
pip install qiskit qiskit-machine-learning
pip install pennylane pennylane-qiskit
pip install dill

# These may take a while to install
```

---

## 🐳 Docker Installation (Alternative)

If you prefer Docker:

```bash
# Build image
docker build -t threat-scanner .

# Run scanner
docker run -it threat-scanner --domain google.com --offline

# Run with API key
docker run -e VT_API_KEY=your_key threat-scanner --domain example.com

# Interactive shell
docker run -it threat-scanner /bin/bash
```

---

## 📊 Post-Installation Verification

Run all these tests to ensure everything works:

```bash
# Test 1: Help
python scanner/threat_scanner.py --help
# ✓ Should display help

# Test 2: Domain scan
python scanner/threat_scanner.py --domain google.com --offline
# ✓ Should complete scan

# Test 3: Check logs
ls scanner/logs/
# ✓ Should see scan_history.json and scan_history.csv

# Test 4: Stats
python scanner/threat_scanner.py --stats
# ✓ Should show statistics

# Test 5: Batch scan
python scanner/threat_scanner.py --domain-file sample_domains.txt
# ✓ Should scan all domains

# Test 6: Python import
python -c "from scanner.modules.domain_scanner import DomainScanner; print('OK')"
# ✓ Should print OK
```

---

## ✅ Installation Complete!

If all tests pass, you're ready to use the scanner!

### Next Steps:
1. **Read the Quick Start**: `QUICKSTART.md`
2. **Try examples**: `USAGE_EXAMPLES.md`
3. **Full documentation**: `SCANNER_README.md`
4. **Deploy**: `DEPLOYMENT.md`

### Common Tasks:
```bash
# Scan a domain
python scanner/threat_scanner.py --domain suspicious.xyz

# Scan a file (offline)
python scanner/threat_scanner.py --file malware.exe --offline

# View scan history
python scanner/threat_scanner.py --stats

# Batch process
python scanner/threat_scanner.py --domain-file domains.txt
```

---

## 💡 Pro Tips

1. **Always use virtual environment** - Keeps dependencies isolated
2. **Set VT API key** - Get better threat intelligence
3. **Check logs regularly** - `scanner/logs/` contains all scan history
4. **Use offline mode** - When internet is slow or unavailable
5. **Update regularly** - `pip install --upgrade -r requirements.txt`

---

## 🆘 Still Having Issues?

1. **Check documentation**: All markdown files in project root
2. **Review logs**: `scanner/logs/` for error messages
3. **Test components**:
   ```bash
   python tests/test_scanner.py
   ```
4. **Check Python version**: `python --version` (needs 3.8+)
5. **Recreate venv**: Sometimes a fresh start helps

---

## 📞 Support Checklist

Before seeking help, have this info ready:
- [ ] Python version: `python --version`
- [ ] OS and version
- [ ] Error message (full traceback)
- [ ] What you were trying to do
- [ ] Output of: `pip list | grep -E "(numpy|scikit|pandas)"`

---

**Happy Scanning!** 🔍🛡️

Installation should take **10-15 minutes** total for a complete setup.
