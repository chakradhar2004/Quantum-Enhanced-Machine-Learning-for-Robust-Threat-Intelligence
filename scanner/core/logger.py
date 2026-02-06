"""
Logging module for Quantum-Enhanced Threat Scanner.
Handles scan history logging to JSON and CSV formats.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from ..config.config import SCAN_LOG_FILE, SCAN_CSV_LOG


class ScanLogger:
    """Handles logging of scan results to JSON and CSV"""
    
    def __init__(self, json_path: Optional[Path] = None, csv_path: Optional[Path] = None):
        """
        Initialize scan logger.
        
        Args:
            json_path: Path to JSON log file (default: from config)
            csv_path: Path to CSV log file (default: from config)
        """
        self.json_path = json_path or SCAN_LOG_FILE
        self.csv_path = csv_path or SCAN_CSV_LOG
        
        # Ensure log files exist
        self._initialize_logs()
    
    def _initialize_logs(self):
        """Create log files if they don't exist"""
        # JSON log
        if not self.json_path.exists():
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_path, 'w') as f:
                json.dump([], f)
        
        # CSV log
        if not self.csv_path.exists():
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'timestamp', 'scan_type', 'target', 'result', 
                    'confidence', 'ml_prediction', 'quantum_analysis',
                    'vt_detections', 'file_hash', 'additional_info'
                ])
                writer.writeheader()
    
    def log_scan(self, scan_data: Dict[str, Any]):
        """
        Log a scan result to both JSON and CSV.
        
        Args:
            scan_data: Dictionary containing scan information with keys:
                - scan_type: 'file' or 'domain'
                - target: file path or domain name
                - result: 'MALICIOUS', 'BENIGN', 'SUSPICIOUS', 'UNKNOWN'
                - confidence: float (0-1)
                - ml_prediction: ML model prediction
                - quantum_analysis: quantum analysis results (optional)
                - vt_detections: VirusTotal detection count (optional)
                - file_hash: file hash (optional)
                - additional_info: any additional information (optional)
        """
        # Add timestamp
        scan_data['timestamp'] = datetime.now().isoformat()
        
        # Log to JSON
        self._log_to_json(scan_data)
        
        # Log to CSV
        self._log_to_csv(scan_data)
    
    def _log_to_json(self, scan_data: Dict[str, Any]):
        """Append scan data to JSON log"""
        try:
            # Read existing data
            with open(self.json_path, 'r') as f:
                logs = json.load(f)
            
            # Append new scan
            logs.append(scan_data)
            
            # Write back
            with open(self.json_path, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not write to JSON log: {e}")
    
    def _log_to_csv(self, scan_data: Dict[str, Any]):
        """Append scan data to CSV log"""
        try:
            # Prepare row data
            row = {
                'timestamp': scan_data.get('timestamp', ''),
                'scan_type': scan_data.get('scan_type', ''),
                'target': scan_data.get('target', ''),
                'result': scan_data.get('result', ''),
                'confidence': scan_data.get('confidence', ''),
                'ml_prediction': scan_data.get('ml_prediction', ''),
                'quantum_analysis': json.dumps(scan_data.get('quantum_analysis', {})) if scan_data.get('quantum_analysis') else '',
                'vt_detections': scan_data.get('vt_detections', ''),
                'file_hash': scan_data.get('file_hash', ''),
                'additional_info': json.dumps(scan_data.get('additional_info', {})) if scan_data.get('additional_info') else ''
            }
            
            # Append to CSV
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                writer.writerow(row)
        except Exception as e:
            print(f"Warning: Could not write to CSV log: {e}")
    
    def get_scan_history(self, limit: Optional[int] = None, scan_type: Optional[str] = None) -> list:
        """
        Retrieve scan history from JSON log.
        
        Args:
            limit: Maximum number of recent scans to retrieve
            scan_type: Filter by scan type ('file' or 'domain')
        
        Returns:
            List of scan records
        """
        try:
            with open(self.json_path, 'r') as f:
                logs = json.load(f)
            
            # Filter by scan type if specified
            if scan_type:
                logs = [log for log in logs if log.get('scan_type') == scan_type]
            
            # Limit results
            if limit:
                logs = logs[-limit:]
            
            return logs
        except Exception as e:
            print(f"Error reading scan history: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics from scan history.
        
        Returns:
            Dictionary containing scan statistics
        """
        try:
            with open(self.json_path, 'r') as f:
                logs = json.load(f)
            
            if not logs:
                return {
                    'total_scans': 0,
                    'file_scans': 0,
                    'domain_scans': 0,
                    'malicious_detected': 0,
                    'benign_detected': 0,
                    'suspicious_detected': 0,
                    'quantum_analyses': 0
                }
            
            stats = {
                'total_scans': len(logs),
                'file_scans': sum(1 for log in logs if log.get('scan_type') == 'file'),
                'domain_scans': sum(1 for log in logs if log.get('scan_type') == 'domain'),
                'malicious_detected': sum(1 for log in logs if log.get('result') == 'MALICIOUS'),
                'benign_detected': sum(1 for log in logs if log.get('result') == 'BENIGN'),
                'suspicious_detected': sum(1 for log in logs if log.get('result') == 'SUSPICIOUS'),
                'quantum_analyses': sum(1 for log in logs if log.get('quantum_analysis'))
            }
            
            return stats
        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return {}
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """
        Export scan history to pandas DataFrame for analysis.
        
        Returns:
            DataFrame containing scan history
        """
        try:
            return pd.read_csv(self.csv_path)
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return pd.DataFrame()


# Global logger instance
_logger = None

def get_logger() -> ScanLogger:
    """Get global logger instance (singleton pattern)"""
    global _logger
    if _logger is None:
        _logger = ScanLogger()
    return _logger
