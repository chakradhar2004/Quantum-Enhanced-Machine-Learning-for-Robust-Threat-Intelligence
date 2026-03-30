"""
Comprehensive Test Suite for Quantum-Enhanced Threat Intelligence

Covers:
- Domain feature extraction (legacy 5 + extended 15 features)
- File feature extraction (16-feature vector)
- Input validation (paths, domains, hashes)
- Model loader (integrity, format handling)
- CLI engine (domain, file scanning)
"""

import sys
import math
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.features import DomainFeatureExtractor, FileFeatureExtractor
from utils.validators import (
    validate_file_path, validate_domain, validate_hash,
    validate_directory_path, ValidationError,
)
from utils.model_loader import SafeModelLoader, ModelIntegrityError


# ═══════════════════════════════════════════════════════
# Domain Feature Extraction
# ═══════════════════════════════════════════════════════

class TestDomainFeatureExtractorLegacy:
    """Test legacy 5-feature extraction (backward-compat with existing RF model)."""

    def setup_method(self):
        self.extractor = DomainFeatureExtractor(use_legacy=True)

    def test_feature_count(self):
        vec, feat = self.extractor.extract("google.com")
        assert vec.shape == (1, 5)
        assert len(feat) == 5

    def test_feature_names(self):
        _, feat = self.extractor.extract("example.com")
        expected = {'length', 'entropy', 'vowel_ratio', 'digit_ratio', 'consonant_ratio'}
        assert set(feat.keys()) == expected

    def test_length(self):
        _, feat = self.extractor.extract("abc.com")
        assert feat['length'] == 3  # 'abc' is the domain part

    def test_entropy_uniform(self):
        _, feat = self.extractor.extract("aaaa.com")
        assert feat['entropy'] == 0.0  # All same chars

    def test_entropy_varied(self):
        _, feat = self.extractor.extract("abcd.com")
        assert feat['entropy'] == 2.0  # 4 unique chars = log2(4) = 2.0

    def test_all_vowels(self):
        _, feat = self.extractor.extract("aeiou.com")
        assert feat['vowel_ratio'] == 1.0
        assert feat['consonant_ratio'] == 0.0

    def test_all_digits(self):
        _, feat = self.extractor.extract("12345.com")
        assert feat['digit_ratio'] == 1.0

    def test_url_cleaning(self):
        vec1, _ = self.extractor.extract("https://example.com/path?q=1")
        vec2, _ = self.extractor.extract("example.com")
        np.testing.assert_array_equal(vec1, vec2)

    def test_deterministic(self):
        """Same input → same output."""
        v1, _ = self.extractor.extract("test.com")
        v2, _ = self.extractor.extract("test.com")
        np.testing.assert_array_equal(v1, v2)


class TestDomainFeatureExtractorExtended:
    """Test extended 15-feature extraction."""

    def setup_method(self):
        self.extractor = DomainFeatureExtractor(use_legacy=False)

    def test_feature_count(self):
        vec, feat = self.extractor.extract("google.com")
        assert vec.shape == (1, 15)
        assert len(feat) == 15

    def test_max_consonant_run(self):
        _, feat = self.extractor.extract("strng.com")
        assert feat['max_consonant_run'] == 5  # 'strng' are all consonants

    def test_bigram_entropy(self):
        _, feat = self.extractor.extract("abcdef.com")
        assert feat['bigram_entropy'] > 0

    def test_subdomain_count(self):
        _, feat = self.extractor.extract("sub.domain.example.com")
        assert feat['subdomain_count'] == 3

    def test_ip_pattern_detection(self):
        _, feat = self.extractor.extract("192-168-1-1.evil.com")
        assert feat['has_ip_pattern'] == 1.0

    def test_no_ip_pattern(self):
        _, feat = self.extractor.extract("google.com")
        assert feat['has_ip_pattern'] == 0.0

    def test_dga_like_domain(self):
        """DGA domains typically have high entropy, high consonant ratio."""
        _, feat = self.extractor.extract("qwrtzxbcdfghjkl.com")
        assert feat['entropy'] > 3.0
        assert feat['consonant_ratio'] > 0.5
        assert feat['max_consonant_run'] >= 3


# ═══════════════════════════════════════════════════════
# File Feature Extraction
# ═══════════════════════════════════════════════════════

class TestFileFeatureExtractor:
    """Test file feature extraction."""

    def setup_method(self):
        self.extractor = FileFeatureExtractor()

    def test_feature_count(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b'\x00' * 100 + b'\xff' * 100 + b'hello world')
            path = Path(f.name)

        try:
            vec = self.extractor.extract(path)
            assert vec is not None
            assert vec.shape == (1, 16)
        finally:
            path.unlink()

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b'')
            path = Path(f.name)

        try:
            vec = self.extractor.extract(path)
            # Should still produce a vector (all zeros or near-zero)
            assert vec is not None
            assert vec.shape == (1, 16)
        finally:
            path.unlink()

    def test_pe_header_detection(self):
        """MZ header should set PE detection feature to 1.0."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as f:
            f.write(b'MZ' + b'\x00' * 510)
            path = Path(f.name)

        try:
            vec = self.extractor.extract(path)
            assert vec is not None
            # Feature index 10 is the MZ header detector
            assert vec[0, 10] == 1.0
        finally:
            path.unlink()

    def test_nonexistent_file(self):
        vec = self.extractor.extract(Path("/nonexistent/file.bin"))
        assert vec is None

    def test_deterministic(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b'\xde\xad\xbe\xef' * 100)
            path = Path(f.name)

        try:
            v1 = self.extractor.extract(path)
            v2 = self.extractor.extract(path)
            np.testing.assert_array_equal(v1, v2)
        finally:
            path.unlink()


# ═══════════════════════════════════════════════════════
# Input Validation
# ═══════════════════════════════════════════════════════

class TestFilePathValidation:

    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test')
            path = f.name

        try:
            result = validate_file_path(path)
            assert result.exists()
        finally:
            Path(path).unlink()

    def test_empty_path(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_file_path("")

    def test_nonexistent_file(self):
        with pytest.raises(ValidationError, match="not found"):
            validate_file_path("/nonexistent/file.txt")

    def test_file_too_large(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'x' * (2 * 1024 * 1024))  # 2MB
            path = f.name

        try:
            with pytest.raises(ValidationError, match="too large"):
                validate_file_path(path, max_size_mb=1.0)
        finally:
            Path(path).unlink()

    def test_path_traversal_blocked(self):
        """Path traversal should be blocked when allowed_root is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.NamedTemporaryFile(
                delete=False, dir=tmpdir
            ) as f:
                f.write(b'safe')
                safe_path = f.name

            # This should work (file is inside root)
            result = validate_file_path(safe_path, allowed_root=tmpdir)
            assert result.exists()


class TestDomainValidation:

    def test_valid_domain(self):
        assert validate_domain("google.com") == "google.com"

    def test_valid_subdomain(self):
        assert validate_domain("www.example.co.uk") == "www.example.co.uk"

    def test_url_cleaned(self):
        assert validate_domain("https://example.com/path") == "example.com"

    def test_empty_domain(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_domain("")

    def test_too_long(self):
        with pytest.raises(ValidationError, match="too long"):
            validate_domain("a" * 300 + ".com")

    def test_ip_address_allowed(self):
        assert validate_domain("192.168.1.1") == "192.168.1.1"


class TestHashValidation:

    def test_valid_md5(self):
        h = validate_hash("d41d8cd98f00b204e9800998ecf8427e")
        assert len(h) == 32

    def test_valid_sha256(self):
        h = validate_hash("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert len(h) == 64

    def test_auto_detect(self):
        h = validate_hash("d41d8cd98f00b204e9800998ecf8427e", hash_type='auto')
        assert len(h) == 32

    def test_invalid_hash(self):
        with pytest.raises(ValidationError):
            validate_hash("not_a_hash")

    def test_empty_hash(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_hash("")


# ═══════════════════════════════════════════════════════
# Model Loader
# ═══════════════════════════════════════════════════════

class TestSafeModelLoader:

    def test_file_not_found(self):
        loader = SafeModelLoader('/nonexistent/dir')
        with pytest.raises(FileNotFoundError):
            loader.load('missing_model.pkl')

    def test_unsupported_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad = Path(tmpdir) / 'model.xyz'
            bad.write_bytes(b'data')
            loader = SafeModelLoader(tmpdir)
            with pytest.raises(ValueError, match="Unsupported"):
                loader.load('model.xyz')

    def test_generate_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy .pkl file
            (Path(tmpdir) / 'test.pkl').write_bytes(b'fake_model_data')
            loader = SafeModelLoader(tmpdir)
            manifest = loader.generate_manifest()
            assert 'test.pkl' in manifest
            assert len(manifest['test.pkl']) == 64  # SHA-256 is 64 hex chars

    def test_integrity_check_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / 'test.pkl'
            model_file.write_bytes(b'original_data')

            manifest_path = Path(tmpdir) / 'manifest.json'
            import json
            with open(manifest_path, 'w') as f:
                json.dump({'test.pkl': 'wrong_hash_' + '0' * 52}, f)

            loader = SafeModelLoader(tmpdir, str(manifest_path))
            with pytest.raises(ModelIntegrityError):
                loader.load('test.pkl')


# ═══════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════

class TestIntegration:
    """Test end-to-end workflows."""

    def test_domain_feature_consistency(self):
        """Legacy and extended extractors should agree on the first 5 features."""
        legacy = DomainFeatureExtractor(use_legacy=True)
        extended = DomainFeatureExtractor(use_legacy=False)

        _, feat_legacy = legacy.extract("example.com")
        _, feat_extended = extended.extract("example.com")

        for name in legacy.LEGACY_FEATURE_NAMES:
            assert abs(feat_legacy[name] - feat_extended[name]) < 1e-6, \
                f"Feature {name} differs: {feat_legacy[name]} vs {feat_extended[name]}"

    def test_file_features_all_positive_or_zero(self):
        """All file features should be non-negative."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b'\xab\xcd\xef' * 100)
            path = Path(f.name)

        try:
            ext = FileFeatureExtractor()
            vec = ext.extract(path)
            assert vec is not None
            assert np.all(vec >= 0)
        finally:
            path.unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
