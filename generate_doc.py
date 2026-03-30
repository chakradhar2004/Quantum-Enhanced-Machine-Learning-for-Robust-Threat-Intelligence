import os
import json

key_files = [
    'main.py',
    'threat_intelligence.py',
    'scanner/threat_scanner.py',
    'scanner/threat_scanner_v2.py',
    'scanner/modules/file_scanner.py',
    'scanner/modules/domain_scanner.py',
    'scanner/modules/quantum_analyzer.py',
    'scanner/core/logger.py',
    'utils/features.py',
    'utils/feature_utils.py',
    'utils/quantum_utils.py',
    'utils/ensemble.py',
    'utils/model_loader.py',
    'utils/validators.py',
    'notebooks/01_feature_engineering.ipynb',
    'notebooks/02_classical_models.ipynb',
    'notebooks/03_quantum_models.ipynb',
    'notebooks/04_inference_cli.ipynb',
    'notebooks/05_phase3_analysis.ipynb',
    'notebooks/06_phase4_quantum_modeling.ipynb',
    'notebooks/07_quick_qsvc_training.ipynb'
]

output_file = 'key_project_code.md'
base_dir = r"d:\final_year_project\Qunatum-Enhanced_Threat_Intelligence"

lines_written = 0
MAX_LINES = 3000

with open(os.path.join(base_dir, output_file), 'w', encoding='utf-8') as outfile:
    def write_line(text):
        global lines_written
        if lines_written < MAX_LINES:
            outfile.write(text)
            lines_written += text.count('\n')
            return True
        return False

    write_line("# Quantum-Enhanced Threat Intelligence - Key Logic Source Code\n\n")
    write_line("This document contains the source code for the key logic files and extracted code from notebooks.\n\n")
    write_line("*(Note: Empty lines and single-line comments have been removed to save space, and the document is capped at 3000 lines)*\n\n")
    
    for relative_path in key_files:
        if lines_written >= MAX_LINES:
            break
            
        file_path = os.path.join(base_dir, relative_path)
        write_line(f"## File: `{relative_path}`\n\n")
        
        if os.path.exists(file_path):
            try:
                if relative_path.endswith('.ipynb'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        notebook = json.load(f)
                    
                    cell_count = 1
                    for cell in notebook.get('cells', []):
                        if lines_written >= MAX_LINES: break
                        if cell.get('cell_type') == 'code':
                            source = cell.get('source', [])
                            if source:
                                clean_source = []
                                for line in source:
                                    if line.strip() and not line.strip().startswith('#'): # Remove empty lines & comments
                                        clean_source.append(line)
                                if clean_source:
                                    write_line(f"#### Notebook Cell {cell_count}\n```python\n")
                                    for line in clean_source:
                                        if not write_line(line if line.endswith('\n') else line + '\n'): break
                                    write_line("```\n\n---\n\n")
                            cell_count += 1
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    clean_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
                    
                    extension = relative_path.split('.')[-1]
                    write_line(f"```{extension}\n")
                    for line in clean_lines:
                        if not write_line(line if line.endswith('\n') else line + '\n'): break
                    write_line("```\n\n---\n\n")
            except Exception as e:
                write_line(f"*Error reading file: {e}*\n\n")
        else:
             write_line("*File not found.*\n\n")

    if lines_written >= MAX_LINES:
        outfile.write("\n\n*Note: Document truncated to ~3000 lines as requested.*\n")

print(f"Created {output_file} successfully! Total lines approx: {lines_written}")
