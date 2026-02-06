# Deployment Checklist - Quantum-Enhanced Threat Scanner

## Pre-Deployment Verification

### ✅ Core Components
- [ ] All models present in `models/` directory
  - [ ] `domain_rf_model.pkl`
  - [ ] `ember_rf_model.pkl`
- [ ] Quantum models in `phase4/models/` (optional)
  - [ ] `qsvc_domain_model.dill`
  - [ ] `vqc_domain_model.dill`
  - [ ] `quantum_scaler.pkl`
- [ ] Scanner modules created
  - [ ] `scanner/modules/file_scanner.py`
  - [ ] `scanner/modules/domain_scanner.py`
  - [ ] `scanner/modules/quantum_analyzer.py`
- [ ] Core functionality
  - [ ] `scanner/core/logger.py`
  - [ ] `scanner/config/config.py`
- [ ] Main application
  - [ ] `scanner/threat_scanner.py`

### ✅ Dependencies
- [ ] `requirements.txt` updated
- [ ] All packages install without errors:
  ```bash
  pip install -r requirements.txt
  ```
- [ ] Optional packages available:
  - [ ] `pefile` (for PE file analysis)
  - [ ] `lief` (alternative PE parser)
  - [ ] `dill` (for quantum models)

### ✅ Testing
- [ ] Unit tests pass:
  ```bash
  python tests/test_scanner.py
  ```
- [ ] Domain scanning works:
  ```bash
  python scanner/threat_scanner.py --domain google.com --offline
  ```
- [ ] File scanning works (if test file available):
  ```bash
  python scanner/threat_scanner.py --file sample.exe --offline
  ```
- [ ] Logging works (check `scanner/logs/` for output files)
- [ ] Statistics display:
  ```bash
  python scanner/threat_scanner.py --stats
  ```

### ✅ Documentation
- [ ] README created (`SCANNER_README.md`)
- [ ] Quick start guide (`QUICKSTART.md`)
- [ ] Usage examples (`USAGE_EXAMPLES.md`)
- [ ] Deployment checklist (this file)

---

## Deployment Options

### Option 1: Standard Python Deployment

#### Requirements
- Python 3.8+
- Virtual environment recommended

#### Steps
1. Clone repository:
   ```bash
   git clone <repository-url>
   cd Qunatum-Enhanced_Threat_Intelligence
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Verify installation:
   ```bash
   python scanner/threat_scanner.py --help
   ```

5. Run first scan:
   ```bash
   python scanner/threat_scanner.py --domain example.com
   ```

#### ✅ Checklist
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Scanner responds to `--help`
- [ ] First scan completes successfully

---

### Option 2: Standalone Executable (PyInstaller)

#### Requirements
- PyInstaller installed:
  ```bash
  pip install pyinstaller
  ```

#### Steps
1. Build executable:
   ```bash
   pyinstaller threat_scanner.spec
   ```
   Or manually:
   ```bash
   pyinstaller --onefile --name ThreatScanner scanner/threat_scanner.py
   ```

2. Executable location:
   - Windows: `dist/ThreatScanner.exe`
   - Linux: `dist/ThreatScanner`

3. Test executable:
   ```bash
   dist/ThreatScanner.exe --help
   dist/ThreatScanner.exe --domain google.com --offline
   ```

4. **Important**: Copy models to executable directory:
   ```bash
   # Create models directory next to executable
   mkdir dist/models
   mkdir -p dist/phase4/models
   
   # Copy model files
   copy models\*.pkl dist\models\
   copy phase4\models\*.dill dist\phase4\models\
   copy phase4\models\*.pkl dist\phase4\models\
   ```

#### ✅ Checklist
- [ ] PyInstaller installed
- [ ] Executable builds without errors
- [ ] Models copied to dist directory
- [ ] Executable runs standalone
- [ ] Test scan completes

---

### Option 3: Docker Deployment

#### Requirements
- Docker installed

#### Steps
1. Build Docker image:
   ```bash
   docker build -t threat-scanner .
   ```

2. Test container:
   ```bash
   docker run -it threat-scanner --help
   docker run -it threat-scanner --domain google.com --offline
   ```

3. Run with volume mounts (for persistent logs):
   ```bash
   docker run -v ./logs:/app/scanner/logs threat-scanner --domain test.com
   ```

4. Interactive mode:
   ```bash
   docker run -it threat-scanner /bin/bash
   ```

#### ✅ Checklist
- [ ] Docker installed
- [ ] Image builds successfully
- [ ] Container runs scanner
- [ ] Volume mounts work
- [ ] Logs persist

---

### Option 4: Production Server Deployment

#### For Web Service Integration

1. Install on server:
   ```bash
   git clone <repo>
   cd Qunatum-Enhanced_Threat_Intelligence
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create systemd service (Linux):
   ```ini
   [Unit]
   Description=Threat Scanner Service
   After=network.target

   [Service]
   Type=simple
   User=scanner
   WorkingDirectory=/opt/threat-scanner
   Environment="PATH=/opt/threat-scanner/venv/bin"
   ExecStart=/opt/threat-scanner/venv/bin/python scanner/threat_scanner.py --daemon

   [Install]
   WantedBy=multi-user.target
   ```

3. Set environment variables:
   ```bash
   export VT_API_KEY=your_api_key
   ```

4. Setup log rotation:
   ```bash
   # /etc/logrotate.d/threat-scanner
   /opt/threat-scanner/scanner/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
   }
   ```

#### ✅ Checklist
- [ ] Server access configured
- [ ] Service installed
- [ ] Environment variables set
- [ ] Log rotation configured
- [ ] Service starts automatically

---

## Post-Deployment Testing

### Functional Tests
```bash
# Test 1: Domain scanning
python scanner/threat_scanner.py --domain google.com --offline

# Test 2: Batch domain scanning
python scanner/threat_scanner.py --domain-file sample_domains.txt

# Test 3: Statistics
python scanner/threat_scanner.py --stats

# Test 4: Offline mode
python scanner/threat_scanner.py --domain test.com --offline

# Test 5: VirusTotal integration (if API key available)
python scanner/threat_scanner.py --domain example.com --vt-key YOUR_KEY
```

### ✅ Post-Deployment Checklist
- [ ] Domain scanning works
- [ ] Batch scanning works
- [ ] Statistics display correctly
- [ ] Logs are created
- [ ] Offline mode works
- [ ] VirusTotal integration works (if enabled)

---

## Security Considerations

### ✅ Security Checklist
- [ ] API keys stored in environment variables (not hardcoded)
- [ ] File upload size limits configured
- [ ] Input validation enabled
- [ ] Logs don't contain sensitive data
- [ ] Scanner runs with minimal privileges
- [ ] Network access restricted (if needed)

### Recommended Configuration
```python
# scanner/config/config.py
MAX_FILE_SIZE_MB = 100  # Limit file size
SUPPORTED_FILE_TYPES = ['.exe', '.dll', '.sys']  # Whitelist file types
```

---

## Monitoring & Maintenance

### Daily Checks
- [ ] Check logs for errors: `scanner/logs/`
- [ ] Monitor disk space (logs can grow)
- [ ] Review scan statistics

### Weekly Maintenance
- [ ] Review malicious detections
- [ ] Update VirusTotal API key if expired
- [ ] Archive old logs

### Monthly Tasks
- [ ] Update dependencies:
  ```bash
  pip install --upgrade -r requirements.txt
  ```
- [ ] Review model performance
- [ ] Update threat signatures (if available)

---

## Troubleshooting Guide

### Issue: Models not found
**Solution**:
```bash
# Verify model files exist
ls models/
ls phase4/models/

# Check paths in config
python -c "from scanner.config.config import *; print(DOMAIN_MODEL_PATH.exists())"
```

### Issue: Import errors
**Solution**:
```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt
```

### Issue: VirusTotal not working
**Solutions**:
1. Check API key: `echo %VT_API_KEY%`
2. Test API: `curl -H "x-apikey: YOUR_KEY" https://www.virustotal.com/api/v3/files/`
3. Use offline mode: `--offline`

### Issue: Slow performance
**Solutions**:
1. Disable quantum: `--no-quantum`
2. Use offline mode: `--offline`
3. Increase confidence threshold in config

---

## Rollback Plan

If deployment fails:

1. Stop scanner service:
   ```bash
   systemctl stop threat-scanner  # Linux
   # Or kill process
   ```

2. Restore previous version:
   ```bash
   git checkout previous-version
   ```

3. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Verify functionality:
   ```bash
   python scanner/threat_scanner.py --help
   ```

---

## Success Criteria

Deployment is successful when:
- [x] Scanner runs without errors
- [x] Domain scanning produces results
- [x] File scanning works (if PE files available)
- [x] Logs are created and populated
- [x] Statistics can be viewed
- [x] Documentation is accessible
- [x] Tests pass

---

## Support & Contact

For issues:
1. Check documentation: `SCANNER_README.md`, `QUICKSTART.md`
2. Review logs: `scanner/logs/`
3. Run tests: `python tests/test_scanner.py`
4. Check examples: `USAGE_EXAMPLES.md`

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Environment**: [ ] Development [ ] Staging [ ] Production
**Status**: [ ] Success [ ] Failed [ ] Partial
