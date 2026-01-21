import pandas as pd
import numpy as np
import tldextract
import string
from collections import Counter
import math
from sklearn.utils import resample


def domain_entropy(domain):
    counts = Counter(domain)
    probs = [v / len(domain) for v in counts.values()]
    return -sum(p * math.log2(p) for p in probs)

def vowel_ratio(domain):
    if len(domain) == 0:
        return 0
    vowels = set('aeiou')
    return sum(1 for c in domain if c in vowels) / len(domain)

def digit_ratio(domain):
    if len(domain) == 0:
        return 0
    return sum(1 for c in domain if c.isdigit()) / len(domain)

def consonant_ratio(domain):
    if len(domain) == 0:
        return 0
    vowels = set('aeiou')
    return sum(1 for c in domain if c.isalpha() and c not in vowels) / len(domain)

def extract_domain_features(df):
    domains = df['domain'].astype(str).str.lower().values
    labels = df['label'].values
    
    features = []
    for domain, label in zip(domains, labels):
        parsed = tldextract.extract(domain)
        main_domain = parsed.domain.lower()
        
        if not main_domain:
            continue 
        
        feat = {
            'length': len(main_domain),
            'entropy': domain_entropy(main_domain),
            'vowel_ratio': vowel_ratio(main_domain),
            'digit_ratio': digit_ratio(main_domain),
            'consonant_ratio': consonant_ratio(main_domain),
            'label': label
            }
        features.append(feat)
        
    return pd.DataFrame(features)

