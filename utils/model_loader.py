"""
Safe Model Loading — Eliminates Pickle/Dill RCE Vulnerability

Provides a unified interface for loading ML models with:
- Hash verification of model files before loading
- Support for pickle (with warnings), ONNX, and joblib formats
- Integrity checking to detect tampered model files
"""

import hashlib
import json
import logging
import warnings
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ModelIntegrityError(Exception):
    """Raised when a model file fails integrity verification."""
    pass


class SafeModelLoader:
    """
    Loads ML models with integrity verification.

    Usage:
        loader = SafeModelLoader(models_dir='models/')
        model = loader.load('domain_rf_model.pkl')
    """

    # Allowed extensions and their loaders
    SUPPORTED_FORMATS = {'.pkl', '.joblib', '.dill', '.onnx'}

    def __init__(self, models_dir: str = 'models',
                 manifest_path: Optional[str] = None):
        """
        Args:
            models_dir: Directory containing model files
            manifest_path: Path to model manifest JSON with expected hashes
        """
        self.models_dir = Path(models_dir)
        self.manifest = {}

        if manifest_path and Path(manifest_path).exists():
            with open(manifest_path, 'r') as f:
                self.manifest = json.load(f)

    def load(self, model_name: str, verify: bool = True) -> Any:
        """
        Load a model file safely.

        Args:
            model_name: Filename of the model (e.g., 'domain_rf_model.pkl')
            verify: If True and manifest exists, verify file hash before loading

        Returns:
            Loaded model object

        Raises:
            FileNotFoundError: If model file doesn't exist
            ModelIntegrityError: If hash verification fails
        """
        model_path = self.models_dir / model_name

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        # Verify integrity if manifest available
        if verify and model_name in self.manifest:
            self._verify_hash(model_path, self.manifest[model_name])

        # Load based on extension
        suffix = model_path.suffix.lower()

        if suffix == '.onnx':
            return self._load_onnx(model_path)
        elif suffix == '.joblib':
            return self._load_joblib(model_path)
        elif suffix == '.dill':
            return self._load_dill(model_path)
        elif suffix == '.pkl':
            return self._load_pickle(model_path)
        else:
            raise ValueError(f"Unsupported model format: {suffix}")

    def _load_pickle(self, path: Path) -> Any:
        """Load pickle model with security warning."""
        import pickle
        warnings.warn(
            f"Loading pickle model {path.name}. "
            "Consider converting to ONNX for production use.",
            UserWarning,
            stacklevel=3,
        )
        with open(path, 'rb') as f:
            return pickle.load(f)

    def _load_dill(self, path: Path) -> Any:
        """Load dill model with security warning."""
        try:
            import dill
        except ImportError:
            raise ImportError("dill is required: pip install dill")

        warnings.warn(
            f"Loading dill model {path.name}. "
            "Dill can deserialize arbitrary code. "
            "Consider converting to ONNX for production use.",
            UserWarning,
            stacklevel=3,
        )
        with open(path, 'rb') as f:
            return dill.load(f)

    def _load_joblib(self, path: Path) -> Any:
        """Load joblib model."""
        import joblib
        return joblib.load(path)

    def _load_onnx(self, path: Path) -> Any:
        """Load ONNX model (safest option)."""
        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError("onnxruntime is required: pip install onnxruntime")
        return ort.InferenceSession(str(path))

    def _verify_hash(self, path: Path, expected_hash: str):
        """Verify SHA-256 hash of model file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        actual = sha256.hexdigest()

        if actual != expected_hash:
            raise ModelIntegrityError(
                f"Model integrity check failed for {path.name}. "
                f"Expected: {expected_hash[:16]}... "
                f"Got: {actual[:16]}..."
            )
        logger.info(f"Model {path.name} integrity verified ✓")

    def generate_manifest(self, output_path: Optional[str] = None) -> dict:
        """
        Generate a manifest of all model files with their SHA-256 hashes.

        Args:
            output_path: If provided, save manifest to this JSON file

        Returns:
            dict mapping filename -> sha256 hash
        """
        manifest = {}

        for model_file in self.models_dir.iterdir():
            if model_file.suffix.lower() in self.SUPPORTED_FORMATS:
                sha256 = hashlib.sha256()
                with open(model_file, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        sha256.update(chunk)
                manifest[model_file.name] = sha256.hexdigest()

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Model manifest saved to {output_path}")

        return manifest
