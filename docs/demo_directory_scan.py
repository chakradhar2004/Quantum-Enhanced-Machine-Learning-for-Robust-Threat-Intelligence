#!/usr/bin/env python3
"""
Directory Scanning Demo
Shows how to scan entire directories for malware
"""

from pathlib import Path
import random
import string

# Create test directory structure
test_dir = Path('test_scan_directory')
test_dir.mkdir(exist_ok=True)

# Create subdirectories
(test_dir / 'documents').mkdir(exist_ok=True)
(test_dir / 'downloads').mkdir(exist_ok=True)
(test_dir / 'system').mkdir(exist_ok=True)

print('Creating test files for directory scan...\n')

# Create benign files
benign_files = [
    ('documents/report.pdf', b'PDF benign content' * 100),
    ('documents/spreadsheet.xlsx', b'XLSX benign content' * 100),
    ('downloads/readme.txt', b'README file benign content' * 50),
    ('system/config.ini', b'CONFIG file' * 100),
]

for file_path, content in benign_files:
    full_path = test_dir / file_path
    full_path.write_bytes(content)
    print(f'✓ Created: {file_path}')

# Create suspicious files (NOP-like patterns)
suspicious_files = [
    ('downloads/suspicious_1.bin', b'\x90' * 1000),  # NOP sled
    ('downloads/suspicious_2.exe', b'\x90\x90\x90' * 500),  # NOP sled
    ('system/suspicious_driver.sys', b'\x90' * 2000),  # NOP sled
]

for file_path, content in suspicious_files:
    full_path = test_dir / file_path
    full_path.write_bytes(content)
    print(f'✓ Created: {file_path}')

print(f'\nTest directory: {test_dir}')
print(f'Total files created: {len(benign_files) + len(suspicious_files)}')
print('\n' + '='*80)
print('RUNNING DIRECTORY SCAN')
print('='*80 + '\n')

# Run the scanner
import subprocess
result = subprocess.run([
    'python', 'scanner/threat_scanner_v2.py',
    '--directory', str(test_dir),
    '--recursive'
], capture_output=False)

print('\n' + '='*80)
print('SCAN COMPLETE - TEST FILES CREATED IN:', test_dir)
print('='*80)
print('\nYou can now run these commands:')
print(f'\n1. Scan all files:')
print(f'   python scanner/threat_scanner_v2.py --directory {test_dir}')
print(f'\n2. Scan only malware:')
print(f'   python scanner/threat_scanner_v2.py --directory {test_dir} --threat-level malware')
print(f'\n3. Scan only .bin and .exe files:')
print(f'   python scanner/threat_scanner_v2.py --directory {test_dir} --extensions bin,exe')
print(f'\n4. Get JSON output:')
print(f'   python scanner/threat_scanner_v2.py --directory {test_dir} --json')
print('\n')
