# Quantum-Enhanced Threat Intelligence

A machine learning system for detecting malicious domains and malware using both classical and quantum-enhanced approaches.

## Project Structure

```
Quantum-Enhanced_Threat_Intelligence/
│
├── data/
│   ├── domains/
│   │   ├── raw/
│   │   │   └── dga-domain.txt          # Raw DGA domain data
│   │   ├── external/
│   │   │   └── top10milliondomains.csv # External benign domain data
│   │   └── processed/
│   │       └── domain_features.csv     # Processed domain features
│   │
│   ├── malware/
│   │   ├── raw/
│   │   │   └── train_features_0.jsonl  # Raw EMBER malware features
│   │   └── processed/
│   │       └── ember_features.csv      # Processed malware features
│
├── models/
│   ├── domain_rf_model.pkl            # Domain classification model
│   └── ember_rf_model.pkl             # Malware classification model
│
├── notebooks/
│   ├── 01_feature_engineering.ipynb   # Feature extraction and preprocessing
│   ├── 02_classical_models.ipynb      # Classical ML model training
│   ├── 03_quantum_models.ipynb        # Quantum-enhanced model training
│   └── 04_inference_cli.ipynb         # Inference examples (optional)
│
├── utils/
│   ├── feature_utils.py               # Feature extraction utilities
│   └── quantum_utils.py               # Quantum computing utilities
│
├── main.py                            # CLI interface for predictions
├── README.md                          # This file
└── requirements.txt                   # Python dependencies
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure data files are in place:
   - DGA domains in `data/domains/raw/dga-domain.txt`
   - Top 10M domains in `data/domains/external/top10milliondomains.csv`
   - EMBER features in `data/malware/raw/train_features_0.jsonl`

## Usage

### Feature Engineering

Run the feature engineering notebook to process raw data:
```bash
jupyter notebook notebooks/01_feature_engineering.ipynb
```

### Model Training

Train classical models:
```bash
jupyter notebook notebooks/02_classical_models.ipynb
```

Train quantum-enhanced models:
```bash
jupyter notebook notebooks/03_quantum_models.ipynb
```

### CLI Inference

Predict if a domain is malicious:
```bash
python main.py domain example.com
```

Predict if a file is malware:
```bash
python main.py malware --features path/to/features.csv
```

## Features

- **Domain Classification**: Detect DGA (Domain Generation Algorithm) domains
- **Malware Detection**: Classify files using EMBER features
- **Quantum-Enhanced Models**: Explore quantum computing for improved detection
- **Classical ML Models**: Random Forest and other classical approaches

## Requirements

- Python 3.8+
- See `requirements.txt` for full list of dependencies

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
