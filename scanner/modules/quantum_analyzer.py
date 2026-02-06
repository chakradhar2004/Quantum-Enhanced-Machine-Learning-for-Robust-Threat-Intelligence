"""
Quantum analyzer module for advanced threat detection.
Handles quantum-enhanced analysis for low-confidence samples.
"""

import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import warnings

try:
    import dill
    DILL_AVAILABLE = True
except ImportError:
    DILL_AVAILABLE = False

from ..config.config import (
    QSVC_MODEL_PATH, VQC_MODEL_PATH, QUANTUM_SCALER_PATH, Colors
)


class QuantumAnalyzer:
    """Handles quantum-enhanced analysis for threat intelligence"""
    
    def __init__(self, use_quantum: bool = True):
        """
        Initialize quantum analyzer.
        
        Args:
            use_quantum: If True, attempt to load quantum models
        """
        self.use_quantum = use_quantum
        self.qsvc_model = None
        self.vqc_model = None
        self.scaler = None
        
        if use_quantum:
            self._load_quantum_models()
    
    def _load_quantum_models(self):
        """Load trained quantum models"""
        if not DILL_AVAILABLE:
            print(f"{Colors.WARNING}⚠ Dill not available. Install with: pip install dill{Colors.ENDC}")
            print(f"{Colors.WARNING}⚠ Quantum analysis will use simulation mode{Colors.ENDC}")
            return
        
        try:
            # Load QSVC model
            if QSVC_MODEL_PATH.exists():
                with open(QSVC_MODEL_PATH, 'rb') as f:
                    self.qsvc_model = dill.load(f)
                print(f"{Colors.OKGREEN}✓ Loaded QSVC quantum model{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ QSVC model not found{Colors.ENDC}")
            
            # Load VQC model
            if VQC_MODEL_PATH.exists():
                with open(VQC_MODEL_PATH, 'rb') as f:
                    self.vqc_model = dill.load(f)
                print(f"{Colors.OKGREEN}✓ Loaded VQC quantum model{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ VQC model not found{Colors.ENDC}")
            
            # Load scaler
            if QUANTUM_SCALER_PATH.exists():
                with open(QUANTUM_SCALER_PATH, 'rb') as f:
                    self.scaler = pickle.load(f)
                print(f"{Colors.OKGREEN}✓ Loaded quantum feature scaler{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Error loading quantum models: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}⚠ Quantum analysis will use simulation mode{Colors.ENDC}")
    
    def preprocess_features(self, features: np.ndarray) -> np.ndarray:
        """
        Preprocess features for quantum analysis.
        Reduces feature dimensionality if needed to match expected scaler input.
        
        Args:
            features: Raw feature vector (can be any dimension)
        
        Returns:
            Preprocessed features (reduced to scaler's expected dimension or 4D)
        """
        # Ensure features are 2D
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # If we have more features than scaler expects, reduce dimensionality
        n_features = features.shape[1]
        
        # Try to get expected feature count from scaler
        expected_features = 4  # Default for quantum models
        if self.scaler is not None:
            try:
                # Try to determine expected features from scaler
                expected_features = self.scaler.n_features_in_
            except:
                expected_features = 4
        
        # Reduce features if needed
        if n_features > expected_features:
            # Use simple averaging to reduce dimensionality
            # Group features into bins and average
            features_reduced = features.reshape(features.shape[0], expected_features, -1).mean(axis=2)
            features = features_reduced
        elif n_features < expected_features:
            # Pad with zeros if we have too few features
            padding = np.zeros((features.shape[0], expected_features - n_features))
            features = np.hstack([features, padding])
        
        # If scaler is available, use it
        if self.scaler is not None:
            try:
                scaled_features = self.scaler.transform(features)
                return scaled_features
            except Exception as e:
                print(f"{Colors.WARNING}⚠ Error scaling features: {e}{Colors.ENDC}")
        
        # Fallback: simple normalization

        # Min-max scaling to [0, 1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            min_vals = np.min(features, axis=1, keepdims=True)
            max_vals = np.max(features, axis=1, keepdims=True)
            
            # Avoid division by zero
            range_vals = max_vals - min_vals
            range_vals[range_vals == 0] = 1
            
            normalized = (features - min_vals) / range_vals
        
        return normalized
    
    def quantum_circuit_simulation(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Simulate quantum circuit analysis (for demonstration when real quantum not available).
        
        Args:
            features: Preprocessed feature vector
        
        Returns:
            Dictionary with simulated quantum analysis results
        """
        # Simulate quantum entanglement and superposition effects
        feature_magnitude = np.linalg.norm(features)
        feature_entropy = -np.sum(np.abs(features) * np.log(np.abs(features) + 1e-10))
        
        # Simulate quantum anomaly score
        anomaly_score = (feature_magnitude * feature_entropy) / (len(features.flatten()) + 1)
        
        # Simulate quantum confidence (inverse of anomaly)
        quantum_confidence = 1.0 / (1.0 + anomaly_score)
        
        # Determine anomaly level
        if anomaly_score > 0.7:
            anomaly_level = "HIGH"
            is_anomalous = True
        elif anomaly_score > 0.4:
            anomaly_level = "MEDIUM"
            is_anomalous = True
        else:
            anomaly_level = "LOW"
            is_anomalous = False
        
        return {
            'method': 'quantum_simulation',
            'anomaly_score': float(anomaly_score),
            'quantum_confidence': float(quantum_confidence),
            'anomaly_level': anomaly_level,
            'is_anomalous': is_anomalous,
            'quantum_features': {
                'entanglement_measure': float(feature_magnitude),
                'quantum_entropy': float(feature_entropy)
            }
        }
    
    def analyze_with_qsvc(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Analyze using Quantum Support Vector Classifier.
        
        Args:
            features: Preprocessed feature vector
        
        Returns:
            Dictionary with QSVC analysis results
        """
        if self.qsvc_model is None:
            return self.quantum_circuit_simulation(features)
        
        try:
            # Ensure features are properly shaped for model
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Flatten to 1D for quantum circuit
            features_flat = features.flatten()
            
            # Get prediction
            prediction = self.qsvc_model.predict(features)[0]
            
            # Try to get probability scores if available
            try:
                proba = self.qsvc_model.predict_proba(features)[0]
                confidence = float(max(proba))
            except:
                # If probabilities not available, use decision function
                try:
                    decision = self.qsvc_model.decision_function(features)[0]
                    confidence = float(1.0 / (1.0 + np.exp(-decision)))  # Sigmoid
                except:
                    confidence = 0.5
            
            return {
                'method': 'qsvc',
                'prediction': int(prediction),
                'confidence': confidence,
                'is_anomalous': bool(prediction == 1),
                'anomaly_level': 'HIGH' if prediction == 1 else 'LOW'
            }
        
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Error with QSVC: {e}{Colors.ENDC}")
            return self.quantum_circuit_simulation(features)
    
    def analyze_with_vqc(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Analyze using Variational Quantum Classifier.
        
        Args:
            features: Preprocessed feature vector
        
        Returns:
            Dictionary with VQC analysis results
        """
        if self.vqc_model is None:
            return self.quantum_circuit_simulation(features)
        
        try:
            # Get prediction
            prediction = self.vqc_model.predict(features)[0]
            
            # Try to get probability scores
            try:
                proba = self.vqc_model.predict_proba(features)[0]
                confidence = float(max(proba))
            except:
                confidence = 0.5
            
            return {
                'method': 'vqc',
                'prediction': int(prediction),
                'confidence': confidence,
                'is_anomalous': bool(prediction == 1),
                'anomaly_level': 'HIGH' if prediction == 1 else 'LOW'
            }
        
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Error with VQC: {e}{Colors.ENDC}")
            return self.quantum_circuit_simulation(features)
    
    def analyze(self, features: np.ndarray, method: str = 'auto') -> Dict[str, Any]:
        """
        Perform quantum analysis on features.
        
        Args:
            features: Feature vector to analyze
            method: 'qsvc', 'vqc', 'simulation', or 'auto'
        
        Returns:
            Dictionary containing quantum analysis results
        """
        print(f"\n{Colors.BOLD}{Colors.HEADER}🔬 Quantum Analysis{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Engaging quantum-enhanced threat detection...{Colors.ENDC}\n")
        
        # Preprocess features
        preprocessed = self.preprocess_features(features)
        
        # Choose analysis method
        if method == 'auto':
            # Use QSVC if available, otherwise VQC, otherwise simulation
            if self.qsvc_model is not None:
                method = 'qsvc'
            elif self.vqc_model is not None:
                method = 'vqc'
            else:
                method = 'simulation'
        
        # Perform analysis
        if method == 'qsvc':
            results = self.analyze_with_qsvc(preprocessed)
        elif method == 'vqc':
            results = self.analyze_with_vqc(preprocessed)
        else:
            results = self.quantum_circuit_simulation(preprocessed)
        
        # Display results
        self._display_results(results)
        
        return results
    
    def _display_results(self, results: Dict[str, Any]):
        """Display quantum analysis results"""
        method = results.get('method', 'unknown').upper()
        print(f"Analysis Method: {Colors.BOLD}{method}{Colors.ENDC}")
        
        if 'anomaly_score' in results:
            score = results['anomaly_score']
            print(f"Anomaly Score: {score:.4f}")
            print(f"Quantum Confidence: {results.get('quantum_confidence', 0):.4f}")
        
        if 'confidence' in results:
            print(f"Confidence: {results['confidence']:.4f}")
        
        anomaly_level = results.get('anomaly_level', 'UNKNOWN')
        is_anomalous = results.get('is_anomalous', False)
        
        if is_anomalous:
            print(f"\n{Colors.FAIL}⚠ ANOMALY DETECTED - Level: {anomaly_level}{Colors.ENDC}")
            print(f"{Colors.FAIL}This sample exhibits unusual quantum patterns{Colors.ENDC}")
        else:
            print(f"\n{Colors.OKGREEN}✓ No significant anomalies detected{Colors.ENDC}")
            print(f"Anomaly Level: {anomaly_level}")
        
        if 'quantum_features' in results:
            qf = results['quantum_features']
            print(f"\nQuantum Features:")
            print(f"  Entanglement Measure: {qf.get('entanglement_measure', 0):.4f}")
            print(f"  Quantum Entropy: {qf.get('quantum_entropy', 0):.4f}")
