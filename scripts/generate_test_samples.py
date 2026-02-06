#!/usr/bin/env python3
"""
Generate realistic PE test samples for malware detection testing.
Creates both benign and malware-like PE files with proper structure.
"""

import struct
import os
from pathlib import Path
import random
import string

class PEGenerator:
    """Generate minimal but valid PE files for testing"""
    
    def __init__(self):
        self.samples_dir = Path("data/samples")
        self.samples_dir.mkdir(exist_ok=True)
    
    def generate_benign_exe(self, filename: str, size_kb: int = 50):
        """Generate a benign-looking PE file"""
        print(f"Generating benign sample: {filename}")
        
        # Minimal DOS header
        dos_header = b'MZ' + b'\x00' * 58 + struct.pack('<I', 0x40)  # PE offset at 0x40
        
        # DOS stub (16 bytes)
        dos_stub = b'\x00' * 16
        
        # PE signature
        pe_signature = b'PE\x00\x00'
        
        # COFF header (20 bytes)
        machine = 0x014C  # i386
        num_sections = 3
        timestamp = 0
        coff_header = struct.pack('<HHIIIHH',
            machine, num_sections, timestamp, 0, 0, 224, 0x0002)  # Characteristics
        
        # Optional header (224 bytes for 32-bit)
        magic = 0x010B  # 32-bit
        optional_header = struct.pack('<H', magic)
        optional_header += b'\x00' * 222  # Simplified
        
        # Section headers (40 bytes each)
        sections = self._create_sections()
        section_data = b''
        for section in sections:
            section_data += section
        
        # Align to 512 bytes (standard PE alignment)
        pe_header_size = len(dos_header) + len(pe_signature) + len(coff_header) + len(optional_header) + len(section_data)
        padding = b'\x00' * (512 - (pe_header_size % 512))
        
        # Add actual file content (benign pattern)
        content_size = size_kb * 1024 - len(dos_header) - len(pe_signature) - len(coff_header) - len(optional_header) - len(section_data)
        benign_content = self._generate_benign_content(content_size)
        
        pe_file = dos_header + pe_signature + coff_header + optional_header + section_data + padding + benign_content
        
        # Write to file
        output_path = self.samples_dir / filename
        with open(output_path, 'wb') as f:
            f.write(pe_file[:size_kb * 1024])  # Ensure size
        
        print(f"  ✓ Created: {output_path} ({os.path.getsize(output_path)} bytes)")
        return str(output_path)
    
    def generate_malware_exe(self, filename: str, size_kb: int = 50):
        """Generate a malware-like PE file with suspicious characteristics"""
        print(f"Generating malware sample: {filename}")
        
        # Minimal DOS header
        dos_header = b'MZ' + b'\x00' * 58 + struct.pack('<I', 0x40)
        
        dos_stub = b'\x00' * 16
        pe_signature = b'PE\x00\x00'
        
        # COFF header
        machine = 0x014C
        num_sections = 4  # More sections = suspicious
        timestamp = 0
        coff_header = struct.pack('<HHIIIHH',
            machine, num_sections, timestamp, 0, 0, 224, 0x0002)
        
        # Optional header
        magic = 0x010B
        optional_header = struct.pack('<H', magic)
        optional_header += b'\x00' * 222
        
        # Section headers for malware-like structure
        sections = self._create_suspicious_sections()
        section_data = b''
        for section in sections:
            section_data += section
        
        pe_header_size = len(dos_header) + len(pe_signature) + len(coff_header) + len(optional_header) + len(section_data)
        padding = b'\x00' * (512 - (pe_header_size % 512))
        
        # Add malware-like content (high entropy, suspicious patterns)
        content_size = size_kb * 1024 - len(dos_header) - len(pe_signature) - len(coff_header) - len(optional_header) - len(section_data)
        malware_content = self._generate_malware_content(content_size)
        
        pe_file = dos_header + pe_signature + coff_header + optional_header + section_data + padding + malware_content
        
        output_path = self.samples_dir / filename
        with open(output_path, 'wb') as f:
            f.write(pe_file[:size_kb * 1024])
        
        print(f"  ✓ Created: {output_path} ({os.path.getsize(output_path)} bytes)")
        return str(output_path)
    
    def _create_sections(self):
        """Create benign-like section headers"""
        sections = []
        
        # .text section
        sections.append(self._create_section_header(b'.text\x00\x00\x00', 0x1000, 0x1000))
        
        # .data section
        sections.append(self._create_section_header(b'.data\x00\x00\x00\x00', 0x2000, 0x1000))
        
        # .rsrc section
        sections.append(self._create_section_header(b'.rsrc\x00\x00\x00', 0x3000, 0x1000))
        
        return sections
    
    def _create_suspicious_sections(self):
        """Create malware-like section headers"""
        sections = []
        
        # Named suspicious sections
        sections.append(self._create_section_header(b'.text\x00\x00\x00', 0x1000, 0x2000))
        sections.append(self._create_section_header(b'.data\x00\x00\x00\x00', 0x3000, 0x2000))
        sections.append(self._create_section_header(b'.rsrc\x00\x00\x00', 0x5000, 0x1000))
        sections.append(self._create_section_header(b'.reloc\x00\x00', 0x6000, 0x1000))  # Suspicious
        
        return sections
    
    def _create_section_header(self, name: bytes, virtual_size: int, raw_size: int):
        """Create a section header (40 bytes)"""
        # Name (8 bytes)
        header = name
        # VirtualSize
        header += struct.pack('<I', virtual_size)
        # VirtualAddress
        header += struct.pack('<I', 0x1000)
        # SizeOfRawData
        header += struct.pack('<I', raw_size)
        # PointerToRawData
        header += struct.pack('<I', 0x400)
        # Characteristics (RWX = suspicious)
        header += struct.pack('<I', 0x60000020)
        # Unused fields
        header += b'\x00' * 16
        
        return header
    
    def _generate_benign_content(self, size: int) -> bytes:
        """Generate benign-looking file content"""
        # Mix of readable strings and normal patterns
        content = b''
        readable = b'kernel32.dll\x00user32.dll\x00GetProcAddress\x00LoadLibrary\x00' * 100
        content += readable
        content += b'\x00' * (size - len(readable))
        return content[:size]
    
    def _generate_malware_content(self, size: int) -> bytes:
        """Generate malware-like content with high entropy and suspicious patterns"""
        # Random high-entropy data (suspicious)
        content = bytes(random.randint(0, 255) for _ in range(size // 2))
        
        # Add suspicious patterns (shellcode-like bytes)
        shellcode = b'\x55\x8B\xEC\x81\xEC\x90\x90\x90\xCC\xCC\xCC'  # NOP sled + INT3
        content += shellcode * (size // (2 * len(shellcode)))
        
        content = content[:size]
        return content
    
    def generate_samples(self):
        """Generate all test samples"""
        print("\n" + "="*60)
        print("Generating PE Test Samples")
        print("="*60 + "\n")
        
        # Benign samples
        self.generate_benign_exe("benign_sample1.exe", 100)
        self.generate_benign_exe("benign_sample2.exe", 50)
        
        # Malware samples
        self.generate_malware_exe("malware_sample1.exe", 100)
        self.generate_malware_exe("malware_sample2.exe", 75)
        
        print("\n" + "="*60)
        print("Sample Generation Complete!")
        print("="*60)
        print(f"\nGenerated files in: {self.samples_dir.absolute()}")
        print("\nNow you can test with:")
        print("  python scanner/threat_scanner.py --file data/samples/malware_sample1.exe --offline")
        print("  python scanner/threat_scanner.py --file data/samples/benign_sample1.exe --offline")

if __name__ == "__main__":
    generator = PEGenerator()
    generator.generate_samples()
