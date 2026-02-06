"""
Threat Intelligence Integration
Lookup file hashes in threat databases and correlate with ML predictions
"""

import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import time

class ThreatIntelligence:
    """Query threat intelligence databases for known malware"""
    
    def __init__(self, virustotal_api_key: Optional[str] = None, 
                 cache_dir: str = 'threat_cache'):
        self.virustotal_api_key = virustotal_api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.virustotal_url = 'https://www.virustotal.com/api/v3/files'
    
    def lookup_hash(self, file_hash: str, hash_type: str = 'sha256') -> Dict[str, Any]:
        """
        Look up file hash in threat databases
        hash_type: 'md5', 'sha1', or 'sha256'
        """
        cache_file = self.cache_dir / f'{file_hash}.json'
        
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        
        result = {
            'hash': file_hash,
            'hash_type': hash_type,
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        if self.virustotal_api_key:
            vt_result = self._query_virustotal(file_hash)
            if vt_result:
                result['sources']['virustotal'] = vt_result
        
        result['sources']['database'] = self._query_local_database(file_hash)
        
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    def _query_virustotal(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Query VirusTotal API for known detections"""
        try:
            headers = {'x-apikey': self.virustotal_api_key}
            response = requests.get(
                f'{self.virustotal_url}/{file_hash}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('data', {}).get('attributes', {})
                
                return {
                    'status': 'found',
                    'detections': attributes.get('last_analysis_stats', {}),
                    'vendors': attributes.get('last_analysis_results', {}),
                    'last_update': attributes.get('last_modification_date')
                }
            elif response.status_code == 404:
                return {'status': 'not_found'}
            else:
                return {'status': 'error', 'code': response.status_code}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _query_local_database(self, file_hash: str) -> Dict[str, Any]:
        """Query local malware hash database"""
        db_path = Path('malware_hashes.json')
        
        if not db_path.exists():
            return {'status': 'no_local_database'}
        
        with open(db_path) as f:
            known_hashes = json.load(f)
        
        if file_hash in known_hashes:
            return {
                'status': 'found',
                'threat_name': known_hashes[file_hash].get('name'),
                'threat_type': known_hashes[file_hash].get('type'),
                'severity': known_hashes[file_hash].get('severity')
            }
        
        return {'status': 'not_found'}
    
    def correlate_with_ml(self, ml_prediction: str, ml_confidence: float,
                         threat_intel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine ML prediction with threat intelligence
        Returns high-confidence verdict
        """
        vt_data = threat_intel.get('sources', {}).get('virustotal', {})
        local_data = threat_intel.get('sources', {}).get('database', {})
        
        vt_detections = 0
        vt_total = 0
        if vt_data.get('status') == 'found':
            stats = vt_data.get('detections', {})
            vt_detections = stats.get('malicious', 0) + stats.get('suspicious', 0)
            vt_total = sum(stats.values())
        
        local_found = local_data.get('status') == 'found'
        
        confidence = ml_confidence
        verdict = ml_prediction
        
        if local_found:
            confidence = 0.99
            verdict = 'MALWARE'
        
        if vt_detections > 5:
            confidence = min(confidence + 0.3, 1.0)
            if verdict == 'UNKNOWN':
                verdict = 'SUSPICIOUS'
        
        return {
            'final_verdict': verdict,
            'final_confidence': float(confidence),
            'ml_verdict': ml_prediction,
            'ml_confidence': ml_confidence,
            'virustotal_detections': vt_detections,
            'virustotal_total': vt_total,
            'local_database_match': local_found,
            'reasoning': self._generate_reasoning(
                ml_prediction, ml_confidence, vt_detections, 
                vt_total, local_found
            )
        }
    
    def _generate_reasoning(self, ml_pred: str, ml_conf: float, 
                           vt_detections: int, vt_total: int, 
                           local_match: bool) -> str:
        """Generate human-readable explanation"""
        if local_match:
            return 'File found in local malware database'
        
        if vt_detections > 5:
            return f'File flagged by {vt_detections}/{vt_total} VirusTotal vendors'
        
        if ml_conf > 0.7 and ml_pred == 'MALWARE':
            return f'ML model high confidence ({ml_conf:.1%}) malware detection'
        
        if ml_conf > 0.5 and ml_pred == 'SUSPICIOUS':
            return f'ML model moderate confidence ({ml_conf:.1%}) suspicious activity'
        
        return 'No strong indicators of compromise detected'


def create_sample_database():
    """Create sample malware hash database for testing"""
    sample_hashes = {
        '84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258': {
            'name': 'Trojan.Generic',
            'type': 'Trojan',
            'severity': 'high'
        },
        '9e60393da455f93b0ec32cf124432651': {
            'name': 'Malware.Dropper',
            'type': 'Dropper',
            'severity': 'critical'
        }
    }
    
    db_path = Path('malware_hashes.json')
    if not db_path.exists():
        with open(db_path, 'w') as f:
            json.dump(sample_hashes, f, indent=2)
        print(f"Created sample database: {db_path}")


if __name__ == '__main__':
    create_sample_database()
    
    ti = ThreatIntelligence()
    
    test_hashes = [
        ('9e60393da455f93b0ec32cf124432651', 'md5'),
        ('84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258', 'sha256'),
    ]
    
    for file_hash, hash_type in test_hashes:
        print(f"\nLooking up {hash_type}: {file_hash}")
        result = ti.lookup_hash(file_hash, hash_type)
        print(json.dumps(result, indent=2))
        
        correlation = ti.correlate_with_ml(
            ml_prediction='MALWARE',
            ml_confidence=0.75,
            threat_intel=result
        )
        print(f"\nCorrelated Result:")
        print(json.dumps(correlation, indent=2))
