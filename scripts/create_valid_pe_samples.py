#!/usr/bin/env python3
"""
Create valid PE files manually.
Generates properly structured PE executables for testing.
"""

import os
from pathlib import Path
import random

def create_simple_benign_pe(filename: str):
    """Create a simple valid benign PE file"""
    print(f"Creating benign PE: {filename}")
    
    # Create minimal but valid PE structure
    pe_data = b'MZ' + b'\x90' * 58 + b'\x40\x00\x00\x00'  # DOS header with PE offset at 0x40
    
    dos_stub = b"This program cannot be run in DOS mode.\r\r\n$\x00\x00\x00"
    pe_data += dos_stub + b'\x00' * (0x40 - len(pe_data))
    
    # PE signature
    pe_data += b'PE\x00\x00'
    
    # COFF header  - minimal
    pe_data += b'\x4c\x01'  # Machine: i386
    pe_data += b'\x02\x00'  # NumberOfSections: 2
    pe_data += b'\x00\x00\x00\x00'  # TimeDateStamp
    pe_data += b'\x00\x00\x00\x00'  # PointerToSymbolTable
    pe_data += b'\x00\x00\x00\x00'  # NumberOfSymbols
    pe_data += b'\xe0\x00'  # SizeOfOptionalHeader: 224
    pe_data += b'\x02\x01'  # Characteristics: EXECUTABLE_IMAGE | MACHINE_32BIT
    
    # Optional header (simplified 32-bit)
    pe_data += b'\x0b\x01'  # Magic: PE32
    pe_data += b'\x0b\x00'  # MajorLinkerVersion
    pe_data += b'\x00' * 218  # Rest of optional header
    
    # Section headers (.text and .data)
    # .text section
    pe_data += b'.text\x00\x00\x00'  # Name
    pe_data += b'\x00\x10\x00\x00'  # VirtualSize: 0x1000
    pe_data += b'\x00\x10\x00\x00'  # VirtualAddress: 0x1000
    pe_data += b'\x00\x10\x00\x00'  # SizeOfRawData: 0x1000
    pe_data += b'\x00\x02\x00\x00'  # PointerToRawData: 0x200
    pe_data += b'\x00' * 16  # Relocations & line numbers
    pe_data += b'\x20\x00\x00\x60'  # Characteristics: CODE | EXECUTABLE | READABLE
    
    # .data section
    pe_data += b'.data\x00\x00\x00\x00'  # Name
    pe_data += b'\x00\x10\x00\x00'  # VirtualSize: 0x1000
    pe_data += b'\x00\x20\x00\x00'  # VirtualAddress: 0x2000
    pe_data += b'\x00\x10\x00\x00'  # SizeOfRawData: 0x1000
    pe_data += b'\x00\x12\x00\x00'  # PointerToRawData: 0x1200
    pe_data += b'\x00' * 16
    pe_data += b'\xc0\x00\x00\xc0'  # Characteristics: INITIALIZED_DATA | READABLE | WRITABLE
    
    # Align to 512
    while len(pe_data) % 512 != 0:
        pe_data += b'\x00'
    
    # Add benign content (low entropy = normal executable patterns)
    benign_content = b'kernel32.dll\x00user32.dll\x00GetProcAddress\x00'
    benign_content += b'\x55\x8b\xec\x83\xec'  # Common x86 prologue
    benign_content += b'\x00' * (0x1000 - len(benign_content))
    
    pe_data += benign_content
    
    # .data section content
    data_content = b'BENIGN_MARKER\x00' + b'\x00' * (0x1000 - 14)
    pe_data += data_content
    
    output_path = Path("data/samples") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(pe_data)
    
    print(f"  ✓ Created: {output_path} ({len(pe_data)} bytes)")
    return str(output_path)

def create_simple_malware_pe(filename: str):
    """Create a simple malware-like PE with suspicious characteristics"""
    print(f"Creating malware PE: {filename}")
    
    # Similar structure but with suspicious content
    pe_data = b'MZ' + b'\x90' * 58 + b'\x40\x00\x00\x00'
    dos_stub = b"This program cannot be run in DOS mode.\r\r\n$\x00\x00\x00"
    pe_data += dos_stub + b'\x00' * (0x40 - len(pe_data))
    
    pe_data += b'PE\x00\x00'
    pe_data += b'\x4c\x01'  # Machine: i386
    pe_data += b'\x03\x00'  # NumberOfSections: 3 (suspicious: more sections)
    pe_data += b'\x00\x00\x00\x00'
    pe_data += b'\x00\x00\x00\x00'
    pe_data += b'\x00\x00\x00\x00'
    pe_data += b'\xe0\x00'  # SizeOfOptionalHeader
    pe_data += b'\x02\x01'  # Characteristics
    
    pe_data += b'\x0b\x01'  # Magic: PE32
    pe_data += b'\x0b\x00'
    pe_data += b'\x00' * 218
    
    # Section headers - add suspicious sections
    sections = [
        (b'.text\x00\x00\x00', 0x1000, 0x1000, 0x200, 0x20000060),
        (b'.data\x00\x00\x00\x00', 0x1000, 0x2000, 0x1200, 0xc0000060),
        (b'.shdata\x00', 0x2000, 0x3000, 0x2200, 0x20000060),  # Suspicious hidden section
    ]
    
    for name, vsize, vaddr, rawptr, chars in sections:
        pe_data += name
        pe_data += b'\x00' * (8 - len(name))  # Pad name
        pe_data += vsize.to_bytes(4, 'little')
        pe_data += vaddr.to_bytes(4, 'little')
        pe_data += vsize.to_bytes(4, 'little')
        pe_data += rawptr.to_bytes(4, 'little')
        pe_data += b'\x00' * 16
        pe_data += chars.to_bytes(4, 'little')
    
    # Align
    while len(pe_data) % 512 != 0:
        pe_data += b'\x00'
    
    # Add malware-like content (high entropy / random)
    malware_content = bytes(random.randint(0, 255) for _ in range(0x1000))
    pe_data += malware_content
    
    # More suspicious patterns
    shellcode = b'\x55\x89\xe5\x81\xec\x90\x90\x90\xcc\xcc' * 50  # Shellcode patterns
    pe_data += shellcode + b'\x00' * (0x1000 - len(shellcode))
    
    # Hidden data
    pe_data += b'\xff' * 0x2000
    
    output_path = Path("data/samples") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(pe_data)
    
    print(f"  ✓ Created: {output_path} ({len(pe_data)} bytes)")
    return str(output_path)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Creating Valid PE Samples")
    print("="*60 + "\n")
    
    # Remove old files
    for old_file in Path("data/samples").glob("*_sample*.exe"):
        if old_file.exists():
            old_file.unlink()
            print(f"Removed old: {old_file.name}")
    
    print()
    
    # Create new samples
    create_simple_benign_pe("benign_pe1.exe")
    create_simple_benign_pe("benign_pe2.exe")
    create_simple_malware_pe("malware_pe1.exe")
    create_simple_malware_pe("malware_pe2.exe")
    
    print("\n" + "="*60)
    print("Test with:")
    print("="*60)
    print("Benign:  python scanner/threat_scanner.py --file data/samples/benign_pe1.exe --offline")
    print("Malware: python scanner/threat_scanner.py --file data/samples/malware_pe1.exe --offline")
    print()
