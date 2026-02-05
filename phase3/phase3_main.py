"""
Phase 3 - Main execution script for quantum-enhanced threat intelligence.
Orchestrates preprocessing, analysis, and visualization.
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

from preprocessing import Phase3Preprocessor, preprocess_domain_dataset, preprocess_malware_dataset
from visualization import Phase3Visualizer
from quantum_kernel import QuantumKernelComparison


def main():
    """Main execution function for Phase 3."""
    
    parser = argparse.ArgumentParser(description='Phase 3: Quantum-Enhanced Threat Intelligence')
    parser.add_argument('--domain', action='store_true', help='Process domain dataset')
    parser.add_argument('--malware', action='store_true', help='Process malware dataset')
    parser.add_argument('--kernel', action='store_true', help='Run quantum kernel analysis')
    parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    parser.add_argument('--all', action='store_true', help='Run all analysis')
    parser.add_argument('--n-components', type=int, default=4, help='Number of PCA components')
    parser.add_argument('--output-dir', type=str, default='../results', help='Output directory')
    
    args = parser.parse_args()
    
    # If no specific option, run all
    if not any([args.domain, args.malware, args.kernel, args.visualize]):
        args.all = True
    
    if args.all:
        args.domain = args.malware = args.kernel = args.visualize = True
    
    print("\n" + "="*70)
    print("PHASE 3: QUANTUM-ENHANCED THREAT INTELLIGENCE")
    print("="*70)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process domain dataset
    if args.domain:
        print("\n[STEP 1] Processing domain dataset...")
        domain_input = '../data/domains/processed/domain_features.csv'
        domain_output = './domain'
        
        if os.path.exists(domain_input):
            try:
                df_domain, _, domain_var = preprocess_domain_dataset(
                    domain_input, domain_output, args.n_components
                )
                print(f"[SUCCESS] Domain dataset processed: {df_domain.shape}")
            except Exception as e:
                print(f"[ERROR] Failed to process domain dataset: {e}")
                return
        else:
            print(f"[WARNING] Domain dataset not found at {domain_input}")
    
    # Process malware dataset
    if args.malware:
        print("\n[STEP 2] Processing malware dataset...")
        malware_input = '../data/malware/processed/ember_features.csv'
        malware_output = './ember'
        
        if os.path.exists(malware_input):
            try:
                df_malware, _, malware_var = preprocess_malware_dataset(
                    malware_input, malware_output, args.n_components
                )
                print(f"[SUCCESS] Malware dataset processed: {df_malware.shape}")
            except Exception as e:
                print(f"[ERROR] Failed to process malware dataset: {e}")
                return
        else:
            print(f"[WARNING] Malware dataset not found at {malware_input}")
    
    # Load processed datasets for further analysis
    domain_pca_path = './domain/domain_pca.csv'
    malware_pca_path = './ember/ember_pca.csv'
    
    if os.path.exists(domain_pca_path):
        df_domain = pd.read_csv(domain_pca_path)
    else:
        print("[ERROR] Domain PCA data not found")
        return
    
    if os.path.exists(malware_pca_path):
        df_malware = pd.read_csv(malware_pca_path)
    else:
        print("[ERROR] Malware PCA data not found")
        return
    
    # Load PCA models
    import pickle
    
    with open('./domain/pca.pkl', 'rb') as f:
        pca_domain = pickle.load(f)
    
    with open('./ember/pca.pkl', 'rb') as f:
        pca_malware = pickle.load(f)
    
    # Quantum kernel analysis
    if args.kernel:
        print("\n[STEP 3] Running quantum kernel analysis...")
        try:
            comparator = QuantumKernelComparison(output_dir=args.output_dir)
            kernel_results = comparator.analyze_and_compare(df_domain, df_malware)
            
            # Save kernel results
            kernel_summary = {
                'domain': {k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                          for k, v in kernel_results['domain'].items()},
                'malware': {k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                           for k, v in kernel_results['malware'].items()}
            }
            
            with open(os.path.join(args.output_dir, 'kernel_analysis.json'), 'w') as f:
                json.dump(kernel_summary, f, indent=4)
            
            print("[SUCCESS] Quantum kernel analysis complete")
        except Exception as e:
            print(f"[ERROR] Kernel analysis failed: {e}")
    
    # Generate visualizations
    if args.visualize:
        print("\n[STEP 4] Generating visualizations...")
        try:
            visualizer = Phase3Visualizer(output_dir=args.output_dir)
            visualizer.plot_all(df_domain, df_malware, pca_domain, pca_malware)
            print("[SUCCESS] Visualizations generated")
        except Exception as e:
            print(f"[ERROR] Visualization failed: {e}")
    
    # Generate summary report
    print("\n[STEP 5] Generating summary report...")
    summary = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'domain': {
            'shape': df_domain.shape,
            'variance_explained': float(sum(pca_domain.explained_variance_ratio_)),
            'class_distribution': df_domain['label'].value_counts().to_dict(),
            'class_percentages': {
                'benign': float(df_domain['label'].value_counts()[0] / len(df_domain) * 100),
                'malicious': float(df_domain['label'].value_counts()[1] / len(df_domain) * 100),
            }
        },
        'malware': {
            'shape': df_malware.shape,
            'variance_explained': float(sum(pca_malware.explained_variance_ratio_)),
            'class_distribution': df_malware['label'].value_counts().to_dict(),
            'class_percentages': {
                'benign': float(df_malware['label'].value_counts()[0] / len(df_malware) * 100),
                'malware': float(df_malware['label'].value_counts()[1] / len(df_malware) * 100),
            }
        }
    }
    
    with open(os.path.join(args.output_dir, 'phase3_summary.json'), 'w') as f:
        json.dump(summary, f, indent=4)
    
    # Print summary
    print("\n" + "="*70)
    print("PHASE 3 EXECUTION SUMMARY")
    print("="*70)
    print(f"\nDomain Dataset:")
    print(f"  Shape: {summary['domain']['shape']}")
    print(f"  Variance explained: {summary['domain']['variance_explained']:.4f}")
    print(f"  Class distribution: {summary['domain']['class_distribution']}")
    
    print(f"\nMalware Dataset:")
    print(f"  Shape: {summary['malware']['shape']}")
    print(f"  Variance explained: {summary['malware']['variance_explained']:.4f}")
    print(f"  Class distribution: {summary['malware']['class_distribution']}")
    
    print(f"\nOutput files saved to: {args.output_dir}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
