#!/usr/bin/env python3
"""
Extract and duplicate REAL PE files from Windows or use system files.
Creates high-confidence test samples using actual PE structure.
"""

import shutil
from pathlib import Path
import struct

def get_system_pe_files():
    """Find real PE files on system"""
    system_paths = [
        Path("C:/Windows/System32/notepad.exe"),
        Path("C:/Windows/System32/calc.exe"),
        Path("C:/Windows/System32/cmd.exe"),
    ]
    
    for path in system_paths:
        if path.exists():
            return path
    return None

def create_benign_from_system():
    """Copy a real system executable as benign sample"""
    print("Creating benign samples from Windows files...")
    
    real_pe = get_system_pe_files()
    if not real_pe:
        print("  ⚠ Windows system files not found, using fallback")
        return False
    
    output_dir = Path("data/samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copy as benign1
        benign1 = output_dir / "benign_windows_1.exe"
        shutil.copy2(real_pe, benign1)
        print(f"  ✓ Created: {benign1} ({benign1.stat().st_size} bytes)")
        
        # Copy as benign2
        benign2 = output_dir / "benign_windows_2.exe"
        shutil.copy2(real_pe, benign2)
        print(f"  ✓ Created: {benign2} ({benign2.stat().st_size} bytes)")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def create_malware_from_benign():
    """Modify benign PE to create malware-like variant"""
    print("\nCreating malware samples by modifying benign files...")
    
    output_dir = Path("data/samples")
    benign_file = output_dir / "benign_windows_1.exe"
    
    if not benign_file.exists():
        print("  ⚠ No benign file to modify")
        return False
    
    try:
        # Read benign file
        with open(benign_file, 'rb') as f:
            data = bytearray(f.read())
        
        # Modify to create malware variant
        # Keep PE header intact, modify data sections with high-entropy content
        if len(data) > 0x1000:
            # Replace data sections with random-looking content
            # This simulates encrypted/obfuscated malware
            import random
            for i in range(0x1000, min(0x2000, len(data))):
                if random.random() < 0.3:  # 30% replacement
                    data[i] = random.randint(0, 255)
        
        # Write malware variants
        malware1 = output_dir / "malware_windows_1.exe"
        with open(malware1, 'wb') as f:
            f.write(data)
        print(f"  ✓ Created: {malware1} ({len(data)} bytes)")
        
        # Create variant 2 with different modification pattern
        data2 = bytearray(data)
        if len(data2) > 0x2000:
            import random
            for i in range(0x2000, min(0x3000, len(data2))):
                if random.random() < 0.5:  # 50% replacement
                    data2[i] = random.randint(0, 255)
        
        malware2 = output_dir / "malware_windows_2.exe"
        with open(malware2, 'wb') as f:
            f.write(data2)
        print(f"  ✓ Created: {malware2} ({len(data2)} bytes)")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def print_summary():
    """Print test instructions"""
    print("\n" + "="*60)
    print("SAMPLES READY FOR TESTING")
    print("="*60)
    print("\nBenign samples (expected: LOW threat):")
    print("  python scanner/threat_scanner.py --file data/samples/benign_windows_1.exe --offline")
    print("  python scanner/threat_scanner.py --file data/samples/benign_windows_2.exe --offline")
    print("\nMalware samples (expected: HIGH/SUSPICIOUS):")
    print("  python scanner/threat_scanner.py --file data/samples/malware_windows_1.exe --offline")
    print("  python scanner/threat_scanner.py --file data/samples/malware_windows_2.exe --offline")
    print("\nCompare confidence scores between benign and malware samples")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Creating Real PE Test Samples")
    print("="*60 + "\n")
    
    success = create_benign_from_system()
    if success:
        create_malware_from_benign()
        print_summary()
    else:
        print("\n⚠ Could not create samples from system files")
        print("Please download EMBER dataset or get real PE files for testing")
