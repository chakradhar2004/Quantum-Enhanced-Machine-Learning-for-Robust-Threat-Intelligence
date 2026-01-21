"""
Main entry point for Quantum-Enhanced Threat Intelligence system.
This script provides CLI interface for model inference and training.
"""

import argparse
import sys
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

# Add utils to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'utils'))

from feature_utils import extract_domain_features


def load_model(model_path):
    """Load a trained model from pickle file."""
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def predict_domain(model_path, domain):
    """Predict if a domain is malicious."""
    model = load_model(model_path)
    
    # Extract features
    df = pd.DataFrame({'domain': [domain]})
    df['label'] = 0  # Dummy label for prediction
    features = extract_domain_features(df)
    
    # Drop label column for prediction
    X = features.drop('label', axis=1)
    
    # Predict
    prediction = model.predict(X)[0]
    probability = model.predict_proba(X)[0]
    
    return prediction, probability


def predict_malware(model_path, features):
    """Predict if a file is malware."""
    model = load_model(model_path)
    prediction = model.predict([features])[0]
    probability = model.predict_proba([features])[0]
    return prediction, probability


def main():
    parser = argparse.ArgumentParser(
        description='Quantum-Enhanced Threat Intelligence CLI'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Domain prediction command
    domain_parser = subparsers.add_parser('domain', help='Predict domain')
    domain_parser.add_argument('domain', type=str, help='Domain to check')
    domain_parser.add_argument(
        '--model',
        type=str,
        default='models/domain_rf_model.pkl',
        help='Path to domain model'
    )
    
    # Malware prediction command
    malware_parser = subparsers.add_parser('malware', help='Predict malware')
    malware_parser.add_argument(
        '--model',
        type=str,
        default='models/ember_rf_model.pkl',
        help='Path to malware model'
    )
    malware_parser.add_argument(
        '--features',
        type=str,
        required=True,
        help='Path to features CSV file'
    )
    
    args = parser.parse_args()
    
    if args.command == 'domain':
        prediction, probability = predict_domain(args.model, args.domain)
        result = "MALICIOUS" if prediction == 1 else "BENIGN"
        print(f"Domain: {args.domain}")
        print(f"Prediction: {result}")
        print(f"Probability: Benign={probability[0]:.3f}, Malicious={probability[1]:.3f}")
        
    elif args.command == 'malware':
        df = pd.read_csv(args.features)
        # Assuming features are in the CSV
        prediction, probability = predict_malware(args.model, df.values[0])
        result = "MALWARE" if prediction == 1 else "BENIGN"
        print(f"Prediction: {result}")
        print(f"Probability: Benign={probability[0]:.3f}, Malware={probability[1]:.3f}")
        
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
