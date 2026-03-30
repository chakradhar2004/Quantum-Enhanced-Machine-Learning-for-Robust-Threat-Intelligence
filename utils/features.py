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
    Extracts features from files for malware detection.
    Produces a consistent 16-feature vector for the EMBER RF model.
    """

    N_FEATURES = 16

    def extract(self, file_path: Path) -> Optional[np.ndarray]:
        """
        Extract features from a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Feature vector shaped (1, 16) or None on failure
        """
        file_path = Path(file_path)

        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            data = self._safe_read(file_path)
        except Exception:
            return None

        # Try PE-specific extraction first
        if LIEF_AVAILABLE:
            try:
                binary = lief.parse(str(file_path))
                if binary is not None:
                    return self._extract_pe_features(binary, data)
            except Exception:
                pass

        # Fallback to generic byte-level features
        return self._extract_generic_features(data)

    def _safe_read(self, file_path: Path, max_bytes: int = 100 * 1024 * 1024) -> bytes:
        """Read file with size limit to prevent OOM."""
        size = file_path.stat().st_size
        if size > max_bytes:
            raise ValueError(f"File too large: {size} bytes > {max_bytes}")
        return file_path.read_bytes()

    def _extract_pe_features(self, binary, data: bytes) -> np.ndarray:
        """Extract features from a parsed PE binary using LIEF."""
        features = []
        file_size = len(data)

        # Byte histogram (8 buckets)
        byte_counts = self._byte_histogram(data, 8)
        features.extend(byte_counts)

        # Entropy-based features
        entropy = self._shannon_entropy(data)
        features.append(entropy / 8.0)
        features.append(min(file_size / 1_000_000, 1.0))
        features.append(1.0 if data[:2] == b'MZ' else 0.0)
        features.append(1.0 if entropy > 7.0 else 0.0)

        # Byte pattern features
        features.append(data.count(b'\x00') / max(file_size, 1))
        features.append(
            sum(1 for b in data if 32 <= b <= 126) / max(file_size, 1)
        )
        features.append(
            sum(1 for b in data if b >= 128) / max(file_size, 1)
        )
        features.append(len(set(data)) / 256.0)

        features = features[:self.N_FEATURES]
        while len(features) < self.N_FEATURES:
            features.append(0.0)

        return np.array(features, dtype=np.float32).reshape(1, -1)

    def _extract_generic_features(self, data: bytes) -> np.ndarray:
        """Extract generic byte-level features from any file."""
        features = []
        file_size = len(data)

        # Byte histogram (8 buckets)
        byte_counts = self._byte_histogram(data, 8)
        features.extend(byte_counts)

        # Entropy and size
        entropy = self._shannon_entropy(data)
        features.append(entropy / 8.0)
        features.append(min(file_size / 1_000_000, 1.0))
        features.append(1.0 if data[:2] == b'MZ' else 0.0)
        features.append(1.0 if entropy > 7.0 else 0.0)

        # Byte pattern features
        features.append(data.count(b'\x00') / max(file_size, 1))
        features.append(
            sum(1 for b in data if 32 <= b <= 126) / max(file_size, 1)
        )
        features.append(
            sum(1 for b in data if b >= 128) / max(file_size, 1)
        )
        features.append(len(set(data)) / 256.0)

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
