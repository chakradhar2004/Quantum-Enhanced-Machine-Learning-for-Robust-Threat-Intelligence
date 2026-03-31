"""
Unified Feature Extraction Pipeline — Single Source of Truth
Eliminates duplicated feature extraction across 4+ files.
"""

import math
import re
import numpy as np
import tldextract
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import lief
    LIEF_AVAILABLE = True
except ImportError:
    LIEF_AVAILABLE = False

try:
    import pefile
    PEFILE_AVAILABLE = True
except ImportError:
    PEFILE_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# Domain Feature Extraction
# ─────────────────────────────────────────────────────────────

class DomainFeatureExtractor:
    """
    Extracts 15 features from a domain name for DGA detection.
    This is the SINGLE place where domain features are defined.
    All scanner modules must import from here.
    """

    # Canonical feature names — order matters for model compatibility
    FEATURE_NAMES = [
        'length',
        'entropy',
        'vowel_ratio',
        'digit_ratio',
        'consonant_ratio',
        'max_consonant_run',
        'bigram_entropy',
        'subdomain_count',
        'tld_length',
        'digit_count',
        'hyphen_count',
        'has_ip_pattern',
        'lexical_diversity',
        'vowel_consonant_transitions',
        'special_char_ratio',
    ]

    # Legacy 5-feature names for backward-compat with existing RF model
    LEGACY_FEATURE_NAMES = [
        'length', 'entropy', 'vowel_ratio', 'digit_ratio', 'consonant_ratio'
    ]

    def __init__(self, use_legacy: bool = False):
        """
        Args:
            use_legacy: If True, extract only the 5 legacy features
                        for backward compatibility with the existing RF model.
        """
        self.use_legacy = use_legacy

    def extract(self, domain: str) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extract features from a domain name or URL.

        Args:
            domain: Domain name or full URL

        Returns:
            (feature_vector shaped (1, n_features), feature_dict)
        """
        # Parse domain from URL if needed
        domain = self._clean_domain(domain)

        # Extract the registrable domain using tldextract
        extracted = tldextract.extract(domain)
        main_domain = extracted.domain.lower()
        full_domain = domain.lower()

        if not main_domain:
            main_domain = domain.lower().split('.')[0]

        features = {}

        # ── Core 5 (legacy-compatible) ───────────────────────
        features['length'] = len(main_domain)
        features['entropy'] = self._shannon_entropy(main_domain)
        features['vowel_ratio'] = self._vowel_ratio(main_domain)
        features['digit_ratio'] = self._digit_ratio(main_domain)
        features['consonant_ratio'] = self._consonant_ratio(main_domain)

        if not self.use_legacy:
            # ── Extended features ────────────────────────────
            features['max_consonant_run'] = self._max_consonant_run(main_domain)
            features['bigram_entropy'] = self._bigram_entropy(main_domain)
            features['subdomain_count'] = full_domain.count('.')
            features['tld_length'] = len(extracted.suffix) if extracted.suffix else 0
            features['digit_count'] = sum(1 for c in main_domain if c.isdigit())
            features['hyphen_count'] = main_domain.count('-')
            features['has_ip_pattern'] = 1.0 if re.search(
                r'\d{1,3}[-_.]\d{1,3}[-_.]\d{1,3}[-_.]\d{1,3}', full_domain
            ) else 0.0
            features['lexical_diversity'] = (
                len(set(main_domain)) / len(main_domain) if main_domain else 0
            )
            features['vowel_consonant_transitions'] = self._vc_transitions(main_domain)
            features['special_char_ratio'] = (
                sum(1 for c in main_domain if not c.isalnum()) / len(main_domain)
                if main_domain else 0
            )

        # Build vector in canonical order
        names = self.LEGACY_FEATURE_NAMES if self.use_legacy else self.FEATURE_NAMES
        vector = np.array(
            [features[n] for n in names], dtype=np.float32
        ).reshape(1, -1)

        return vector, features

    # ── helper methods ───────────────────────────────────────

    @staticmethod
    def _clean_domain(domain: str) -> str:
        """Strip protocol, path, port from a domain/URL."""
        domain = domain.strip()
        if '://' in domain:
            domain = domain.split('://')[1]
        domain = domain.split('/')[0]
        domain = domain.split(':')[0]
        return domain

    @staticmethod
    def _shannon_entropy(text: str) -> float:
        if not text:
            return 0.0
        counts = Counter(text)
        probs = [v / len(text) for v in counts.values()]
        return -sum(p * math.log2(p) for p in probs)

    @staticmethod
    def _vowel_ratio(domain: str) -> float:
        if not domain:
            return 0.0
        vowels = set('aeiou')
        return sum(1 for c in domain.lower() if c in vowels) / len(domain)

    @staticmethod
    def _digit_ratio(domain: str) -> float:
        if not domain:
            return 0.0
        return sum(1 for c in domain if c.isdigit()) / len(domain)

    @staticmethod
    def _consonant_ratio(domain: str) -> float:
        if not domain:
            return 0.0
        vowels = set('aeiou')
        return sum(
            1 for c in domain.lower() if c.isalpha() and c not in vowels
        ) / len(domain)

    @staticmethod
    def _max_consonant_run(domain: str) -> int:
        """Longest consecutive consonant sequence — strong DGA indicator."""
        vowels = set('aeiouAEIOU')
        max_run = 0
        current = 0
        for c in domain:
            if c.isalpha() and c not in vowels:
                current += 1
                max_run = max(max_run, current)
            else:
                current = 0
        return max_run

    @staticmethod
    def _bigram_entropy(text: str) -> float:
        """Shannon entropy of character bigrams."""
        if len(text) < 2:
            return 0.0
        bigrams = [text[i:i+2] for i in range(len(text) - 1)]
        counts = Counter(bigrams)
        total = len(bigrams)
        probs = [v / total for v in counts.values()]
        return -sum(p * math.log2(p) for p in probs)

    @staticmethod
    def _vc_transitions(domain: str) -> int:
        """Count transitions between vowels and consonants."""
        vowels = set('aeiou')
        transitions = 0
        prev_is_vowel = None
        for c in domain.lower():
            if not c.isalpha():
                prev_is_vowel = None
                continue
            is_vowel = c in vowels
            if prev_is_vowel is not None and is_vowel != prev_is_vowel:
                transitions += 1
            prev_is_vowel = is_vowel
        return transitions


# ─────────────────────────────────────────────────────────────
# File Feature Extraction
# ─────────────────────────────────────────────────────────────

class FileFeatureExtractor:
    """
    Extracts EMBER-compatible PE features from files for malware detection.
    Produces a consistent 16-feature vector matching EMBER RF model training.

    Features (after one-hot encoding of machine type):
    - file_size
    - has_signature
    - machine_type (one-hot: ???, AMD64, ARM, ARMNT, I386, IA64, POWERPC, R4000, SH3, SH4, THUMB)
    - characteristics_count
    - histogram_sum
    - entropy_mean
    """

    N_FEATURES = 16

    # Machine types one-hot encoding (11 types total)
    MACHINE_TYPES = {
        0x0: 'UNKNOWN',      # ???
        0x014c: 'I386',
        0x0160: 'R4000',
        0x0162: 'ARMNT',
        0x0168: 'MIPS16',
        0x0169: 'MIPSFPU',
        0x016a: 'MIPSFPU16',
        0x0183: 'SH3',
        0x0184: 'SH4',
        0x0185: 'THUMB',
        0x01c2: 'MIPSX',
        0x0240: 'ARM64',
        0x0266: 'MIPS16',
        0x0366: 'MIPSFPU',
        0x0466: 'MIPSFPU16',
        0x0520: 'TRICORE',
        0x0660: 'HEXAGON',
        0x0be0: 'ALPHA64',
        0x0ebc: 'ARM64',
        0xf32d: 'RISCV32',
        0xf33d: 'RISCV64',
        0xf34d: 'RISCV128',
        0x8664: 'AMD64',
        0xc0ee: 'CEEMIPS',
        0x9041: 'M32R',
        0x4d4d: 'ARM',
        0xa641: 'ARM64',
    }

    MACHINE_NAMES_ORDER = ['???', 'AMD64', 'ARM', 'ARMNT', 'I386', 'IA64', 'POWERPC', 'R4000', 'SH3', 'SH4', 'THUMB']

    def extract(self, file_path: Path) -> Optional[np.ndarray]:
        """
        Extract EMBER-compatible features from a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Feature vector shaped (1, 16) with EMBER-compatible features or None on failure
        """
        file_path = Path(file_path)

        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            data = self._safe_read(file_path)
        except Exception:
            return None

        # Try PE-specific extraction using pefile
        if PEFILE_AVAILABLE:
            try:
                pe = pefile.PE(str(file_path), fast_load=True)
                features_out = self._extract_pe_features_pefile(pe, data)
                pe.close()
                return features_out
            except Exception:
                pass

        # Try LIEF fallback
        if LIEF_AVAILABLE:
            try:
                binary = lief.parse(str(file_path))
                if binary is not None:
                    return self._extract_pe_features_lief(binary, data)
            except Exception:
                pass

        # Strict validation: Do NOT fallback to generic features. Return None for non-PE.
        return None

    def _safe_read(self, file_path: Path, max_bytes: int = 100 * 1024 * 1024) -> bytes:
        """Read file with size limit to prevent OOM."""
        size = file_path.stat().st_size
        if size > max_bytes:
            raise ValueError(f"File too large: {size} bytes > {max_bytes}")
        return file_path.read_bytes()

    def _extract_pe_features_pefile(self, pe, data: bytes) -> np.ndarray:
        """Extract EMBER features from PE using pefile library."""
        features = []

        # 1. file_size
        file_size = float(len(data))
        features.append(file_size)

        # 2. has_signature (check for certificate directory)
        has_signature = 0.0
        if hasattr(pe, 'DIRECTORY_ENTRY_DEBUG') or \
           hasattr(pe, 'DIRECTORY_ENTRY_SECURITY'):
            has_signature = 1.0
        features.append(has_signature)

        # 3. characteristics_count
        characteristics = pe.FILE_HEADER.Characteristics if hasattr(pe, 'FILE_HEADER') else 0
        char_count = bin(characteristics).count('1')
        features.append(float(char_count))

        # 4. histogram_sum (should be file_size, but calculating byte histogram sum)
        features.append(file_size)

        # 5. entropy_mean
        entropy = self._shannon_entropy(data)
        features.append(entropy)


        # 6-16. machine type (one-hot encoding 11 types)
        machine_type = pe.FILE_HEADER.Machine if hasattr(pe, 'FILE_HEADER') else 0
        machine_name = self._get_machine_name(machine_type)

        for name in self.MACHINE_NAMES_ORDER:
            features.append(1.0 if machine_name == name else 0.0)

        # Ensure exactly 16 features
        features = features[:self.N_FEATURES]
        while len(features) < self.N_FEATURES:
            features.append(0.0)

        return np.array(features, dtype=np.float32).reshape(1, -1)

    def _extract_pe_features_lief(self, binary, data: bytes) -> np.ndarray:
        """Extract EMBER features from PE using LIEF library."""
        features = []

        # 1. file_size
        file_size = float(len(data))
        features.append(file_size)

        # 2. has_signature
        has_signature = 1.0 if binary.has_authenticode() else 0.0
        features.append(has_signature)

        # 3. characteristics_count
        char_count = len(binary.header.characteristics) if hasattr(binary.header, 'characteristics') else 0
        features.append(float(char_count))

        # 4. histogram_sum
        features.append(file_size)

        # 5. entropy_mean
        entropy = self._shannon_entropy(data)
        features.append(entropy)


        # 6-16. machine type (one-hot encoding)
        machine = binary.header.machine if hasattr(binary.header, 'machine') else 0
        machine_name = self._get_machine_name(machine)

        for name in self.MACHINE_NAMES_ORDER:
            features.append(1.0 if machine_name == name else 0.0)

        # Ensure exactly 16 features
        features = features[:self.N_FEATURES]
        while len(features) < self.N_FEATURES:
            features.append(0.0)

        return np.array(features, dtype=np.float32).reshape(1, -1)

    def _get_machine_name(self, machine_type: int) -> str:
        """Map machine type constant to name."""
        mapping = {
            0x0: '???',
            0x014c: 'I386',
            0x0160: 'R4000',
            0x0162: 'ARMNT',
            0x0183: 'SH3',
            0x0184: 'SH4',
            0x0185: 'THUMB',
            0x0200: 'POWERPC',
            0x0268: 'ARM',
            0x0366: 'MIPSFPU',
            0x0ebc: 'ARM64',
            0x8664: 'AMD64',
            0x9041: 'M32R',
        }
        if machine_type in mapping:
            return mapping[machine_type]

        # Try to match by name attribute
        machine_name_map = {
            'I386': 'I386',
            'R4000': 'R4000',
            'ARMNT': 'ARMNT',
            'SH3': 'SH3',
            'SH4': 'SH4',
            'THUMB': 'THUMB',
            'POWERPC': 'POWERPC',
            'ARM': 'ARM',
            'IA64': 'IA64',
            'AMD64': 'AMD64',
        }

        for k, v in machine_name_map.items():
            if k in str(machine_type).upper():
                return v

        return '???'

    def _extract_generic_features(self, data: bytes) -> np.ndarray:
        """Extract generic features when PE parsing fails."""
        features = []
        file_size = float(len(data))

        # 1. file_size
        features.append(file_size)

        # 2. has_signature (check for common signature patterns)
        has_sig = 1.0 if b'Signature' in data or b'PKCS' in data else 0.0
        features.append(has_sig)

        # 3. characteristics_count (estimate from file structure)
        char_count = 5.0 if data[:2] == b'MZ' else 0.0
        features.append(char_count)

        # 4. histogram_sum (file_size)
        features.append(file_size)

        # 5. entropy_mean
        entropy = self._shannon_entropy(data)
        features.append(entropy)


        # 6-16. machine type (default to ??? for all)
        for name in self.MACHINE_NAMES_ORDER:
            features.append(1.0 if name == '???' else 0.0)

        # Ensure exactly 16 features
        features = features[:self.N_FEATURES]
        while len(features) < self.N_FEATURES:
            features.append(0.0)

        return np.array(features, dtype=np.float32).reshape(1, -1)

    @staticmethod
    def _byte_histogram(data: bytes, bins: int = 8) -> List[float]:
        if not data:
            return [0.0] * bins
        hist = [0] * 256
        for byte in data:
            hist[byte] += 1
        bytes_per_bin = 256 // bins
        result = []
        for i in range(bins):
            start = i * bytes_per_bin
            end = (i + 1) * bytes_per_bin
            result.append(sum(hist[start:end]) / len(data))
        return result

    @staticmethod
    def _shannon_entropy(data: bytes) -> float:
        if not data:
            return 0.0
        counts = Counter(data)
        length = len(data)
        return -sum(
            (c / length) * math.log2(c / length) for c in counts.values()
        )
