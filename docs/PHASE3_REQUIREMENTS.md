# Phase 3 Requirements

Phase 3 uses the following Python packages (all standard ML libraries):

## Core Dependencies
```
pandas>=1.3.0          # Data manipulation
numpy>=1.21.0          # Numerical computing
scikit-learn>=1.0.0    # Machine learning, PCA, preprocessing
matplotlib>=3.4.0      # Plotting and visualization
seaborn>=0.11.0        # Statistical visualization
```

## Installation

### Option 1: Add to existing requirements.txt
```bash
pip install pandas>=1.3.0 numpy>=1.21.0 scikit-learn>=1.0.0 matplotlib>=3.4.0 seaborn>=0.11.0
```

### Option 2: Create Phase 3 specific requirements
Save as `phase3_requirements.txt`:
```
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=1.0.0
matplotlib>=3.4.0
seaborn>=0.11.0
```

Then install:
```bash
pip install -r phase3_requirements.txt
```

### Option 3: Use conda
```bash
conda install pandas numpy scikit-learn matplotlib seaborn
```

## Verification

Check if all dependencies are installed:
```python
import pandas as pd
import numpy as np
import sklearn
import matplotlib.pyplot as plt
import seaborn as sns

print("✓ All Phase 3 dependencies installed!")
```

## Optional Dependencies

For enhanced functionality (not required):

```
jupyter>=1.0.0         # Interactive notebooks
ipython>=7.0.0         # IPython kernel
plotly>=5.0.0          # Interactive plots
kaleido>=0.2.1         # Export plots to images
```

## Notes

- All dependencies are available in standard Python environments
- No GPU required
- Works on Windows, macOS, Linux
- Python 3.8+ recommended
- scikit-learn is the main computational dependency

## Verification Command

```bash
cd phase3
python -c "from phase3 import Phase3Preprocessor, Phase3Visualizer; print('✓ Phase 3 ready!')"
```
