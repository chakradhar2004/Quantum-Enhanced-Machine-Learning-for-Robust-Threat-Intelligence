import json
from threat_intelligence import ThreatIntelligence, create_sample_database

# Create sample database with provided hashes
create_sample_database()

# Initialize threat intelligence
ti = ThreatIntelligence()

# Provided hashes
hashes = {
    'sha256': '84b484fd3636f2ca3e468d2821d97aacde8a143a2724a3ae65f48a33ca2fd258',
    'md5': '9e60393da455f93b0ec32cf124432651'
}

print('='*70)
print('THREAT INTELLIGENCE LOOKUP TEST')
print('='*70)

# Look up by SHA256
print(f'\n1. Looking up SHA256: {hashes["sha256"]}')
result_sha256 = ti.lookup_hash(hashes['sha256'], 'sha256')
print(json.dumps(result_sha256, indent=2))

# Correlate with ML prediction
print(f'\n2. Correlating with ML prediction...')
correlation = ti.correlate_with_ml(
    ml_prediction='MALWARE',
    ml_confidence=0.75,
    threat_intel=result_sha256
)
print(json.dumps(correlation, indent=2))

# Look up by MD5
print(f'\n3. Looking up MD5: {hashes["md5"]}')
result_md5 = ti.lookup_hash(hashes['md5'], 'md5')
print(json.dumps(result_md5, indent=2))

print('\n' + '='*70)
print('Database created at: malware_hashes.json')
print('='*70)
