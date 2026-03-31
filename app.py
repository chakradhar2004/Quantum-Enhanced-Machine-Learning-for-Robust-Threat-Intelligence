import streamlit as st
import pandas as pd
import time
import os
import tempfile
from pathlib import Path
import sys

# Add project root to sys path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner.threat_scanner import ThreatScanner

# Initialize page config
st.set_page_config(
    page_title="Quantum-Enhanced Threat Scanner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark cybersecurity theme custom CSS
st.markdown("""
<style>
    /* Force dark theme elements for Streamlit */
    .stApp {
        background-color: #0E1117;
        color: #C9D1D9;
    }
    .main-title {
        color: #58A6FF;
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
        text-shadow: 0 0 5px rgba(88, 166, 255, 0.5);
    }
    .verdict-malicious {
        color: #FF7B72;
        font-size: 32px;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(255, 123, 114, 0.7);
    }
    .verdict-benign {
        color: #3FB950;
        font-size: 32px;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(63, 185, 80, 0.7);
    }
    .verdict-suspicious {
        color: #D2A8FF;
        font-size: 32px;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(210, 168, 255, 0.7);
    }
    .confidence-high {
        font-size: 40px;
        font-weight: bold;
        color: #F0F6FC;
        margin-top: -15px;
    }
    .info-container {
        border-left: 5px solid #58A6FF;
        padding-left: 15px;
        margin-top: 20px;
        background-color: #161B22;
        padding: 15px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Loading Models...")
def get_scanner():
    """Load the models once using ThreatScanner backend to handle caching"""
    vt_key = os.environ.get("VT_API_KEY", None)
    # Using offline_mode=True skips virus total checks if VT_API_KEY is not set
    return ThreatScanner(vt_api_key=vt_key, offline_mode=vt_key is None)

if 'scan_history' not in st.session_state:
    st.session_state.scan_history = []

def log_scan(scan_type, target, verdict, confidence, model_used):
    """Maintain scan history in memory session state"""
    st.session_state.scan_history.append({
        "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Type": scan_type,
        "Target": target,
        "Verdict": verdict,
        "Confidence (%)": round(confidence * 100, 2),
        "Model": model_used
    })

def render_file_scanner(scanner):
    st.markdown('<h2 class="main-title">File Scanner 🔍</h2>', unsafe_allow_html=True)
    st.write("Upload an executable file (.exe, .dll) to scan for malware using Ember and Quantum Models.")
    
    uploaded_file = st.file_uploader("Choose a file to scan", type=['exe', 'dll', 'bin'])
    
    if uploaded_file is not None and st.button("Analyze Threat", type="primary"):
        with st.spinner("Analyzing threat..."):
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name
            
            try:
                progress_bar = st.progress(0)
                time.sleep(0.3)
                progress_bar.progress(30)
                
                # 1. Run ML scan
                results = scanner.file_scanner.scan_file(tmp_path)
                progress_bar.progress(60)
                
                if 'error' in results:
                    st.error(f"Scan failed: {results['error']}")
                    return
                
                prediction = results.get('ml_prediction', 'UNKNOWN')
                confidence = results.get('ml_confidence', 0.0)
                
                model_used = "Random Forest (Classical)"
                final_verdict = prediction
                final_confidence = confidence
                
                # 2. Check if we need Quantum Analysis (Confidence between 0.5 and 0.7)
                if results.get('needs_quantum_analysis', False):
                    st.warning(f"Confidence ambiguous ({confidence:.2%}). Engaging Quantum Support Vector Classifier (QSVC) to clarify...")
                    features = scanner.file_scanner.extract_pe_features(Path(tmp_path))
                    
                    if features is not None:
                        q_results = scanner.quantum_analyzer.analyze(features, method='qsvc')
                        model_used = "RF + QSVC (Ensemble)"
                        
                        q_conf = q_results.get('confidence', q_results.get('quantum_confidence', 0.0))
                        
                        # Combine results using formula: final_score = (ml_prob * 0.7) + (quantum_prob * 0.3)
                        final_confidence = (confidence * 0.7) + (q_conf * 0.3)
                        
                        if final_confidence >= 0.7:
                            final_verdict = "MALICIOUS"
                        elif final_confidence >= 0.5:
                            final_verdict = "SUSPICIOUS"
                        else:
                            final_verdict = "BENIGN"
                    else:
                        st.error("Failed to extract features for quantum analysis.")
                        
                progress_bar.progress(100)
                
                # Render results
                st.subheader("Analysis Results")
                if final_verdict == "MALICIOUS":
                    sys_verdict = "❌ MALICIOUS"
                    st.markdown(f'<p class="verdict-malicious">{sys_verdict}</p>', unsafe_allow_html=True)
                elif final_verdict == "BENIGN":
                    sys_verdict = "✅ BENIGN"
                    st.markdown(f'<p class="verdict-benign">{sys_verdict}</p>', unsafe_allow_html=True)
                elif final_verdict == "UNKNOWN":
                    sys_verdict = "❓ UNKNOWN"
                    st.markdown(f'<p class="verdict-suspicious">{sys_verdict}</p>', unsafe_allow_html=True)
                else:
                    sys_verdict = "⚠ SUSPICIOUS"
                    st.markdown(f'<p class="verdict-suspicious">{sys_verdict}</p>', unsafe_allow_html=True)
                
                st.markdown(f'<p class="confidence-high">{final_confidence*100:.1f}% Confidence</p>', unsafe_allow_html=True)
                
                st.markdown('<div class="info-container">', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Model Used:** {model_used}")
                    st.write(f"**File Size:** {results.get('file_size_mb', 0):.2f} MB")
                with col2:
                    st.write(f"**SHA256:** `{results.get('hashes', {}).get('sha256', 'N/A')}`")
                    st.write(f"**MD5:** `{results.get('hashes', {}).get('md5', 'N/A')}`")
                st.markdown('</div>', unsafe_allow_html=True)
                
                log_scan("File", uploaded_file.name, final_verdict, final_confidence, model_used)
                
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except PermissionError:
                        # Windows may hold pefile locks, allow temp file trailing accumulation
                        pass


def render_domain_scanner(scanner):
    st.markdown('<h2 class="main-title">Domain Scanner 🌐</h2>', unsafe_allow_html=True)
    st.write("Enter a domain name to scan for Domain Generation Algorithms (DGA) or contextual malicious indicators.")
    
    domain_input = st.text_input("Target Domain", placeholder="e.g., example.com or suspicious-dga123.net")
    
    if st.button("Analyze Threat", type="primary") and domain_input:
        with st.spinner("Analyzing threat..."):
            progress_bar = st.progress(0)
            time.sleep(0.3)
            progress_bar.progress(30)
            
            # 1. Run ML domain scan
            results = scanner.domain_scanner.scan_domain(domain_input)
            progress_bar.progress(60)
            
            prediction = results.get('ml_prediction', 'UNKNOWN')
            confidence = results.get('ml_confidence', 0.0)
            
            model_used = "Random Forest (Classical)"
            final_verdict = prediction
            final_confidence = confidence
            
            # 2. Check Quantum Analysis exactly as File Scanner
            if results.get('needs_quantum_analysis', False):
                st.warning(f"Confidence ambiguous ({confidence:.2%}). Engaging Quantum Support Vector Classifier (QSVC) for domain anomalies...")
                try:
                    features, feature_dict = scanner.domain_scanner.extract_domain_features(domain_input)
                    if feature_dict is not None:
                        # QSVC exclusively trained on 4 specific features
                        qsvc_features = [
                            feature_dict.get('length', 0),
                            feature_dict.get('entropy', 0),
                            feature_dict.get('vowel_ratio', 0),
                            feature_dict.get('digit_ratio', 0)
                        ]
                        
                        import numpy as np
                        if len(qsvc_features) == 4:
                            X_q = np.array(qsvc_features).reshape(1, -1)
                            q_results = scanner.quantum_analyzer.analyze(X_q, method='qsvc')
                            model_used = "RF + QSVC (Ensemble)"
                            
                            q_conf = q_results.get('confidence', q_results.get('quantum_confidence', 0.0))
                            
                            # Combine results using formula: final_score = (ml_prob * 0.7) + (quantum_prob * 0.3)
                            final_confidence = (confidence * 0.7) + (q_conf * 0.3)
                            
                            if final_confidence >= 0.7:
                                final_verdict = "MALICIOUS"
                            elif final_confidence >= 0.5:
                                final_verdict = "SUSPICIOUS"
                            else:
                                final_verdict = "BENIGN"
                        else:
                            st.error("Quantum feature mismatch. Skipping QSVC.")
                except Exception as e:
                    st.error(f"Quantum extraction error: {e}")
            
            progress_bar.progress(100)
            
            st.subheader("Analysis Results")
            if final_verdict == "MALICIOUS":
                 sys_verdict = "❌ MALICIOUS"
                 st.markdown(f'<p class="verdict-malicious">{sys_verdict}</p>', unsafe_allow_html=True)
            elif final_verdict == "BENIGN":
                 sys_verdict = "✅ BENIGN"
                 st.markdown(f'<p class="verdict-benign">{sys_verdict}</p>', unsafe_allow_html=True)
            elif final_verdict == "UNKNOWN":
                 sys_verdict = "❓ UNKNOWN"
                 st.markdown(f'<p class="verdict-suspicious">{sys_verdict}</p>', unsafe_allow_html=True)
            else:
                 sys_verdict = "⚠ SUSPICIOUS"
                 st.markdown(f'<p class="verdict-suspicious">{sys_verdict}</p>', unsafe_allow_html=True)
            
            st.markdown(f'<p class="confidence-high">{final_confidence*100:.1f}% Confidence</p>', unsafe_allow_html=True)
            
            st.markdown('<div class="info-container">', unsafe_allow_html=True)
            st.write(f"**Target:** `{domain_input}`")
            st.write(f"**Model Used:** {model_used}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if 'features' in results:
                with st.expander("View Extracted Domain Features", expanded=False):
                    st.json(results['features'])
                
            log_scan("Domain", domain_input, final_verdict, final_confidence, model_used)

def render_history():
    st.markdown('<h2 class="main-title">Scan History 📜</h2>', unsafe_allow_html=True)
    if not st.session_state.scan_history:
        st.info("No scans performed yet in this session.")
    else:
        df = pd.DataFrame(st.session_state.scan_history)
        # Add visual enhancements to dataframe depending on verdict
        def style_verdict(val):
            if val == "MALICIOUS":
                return 'background-color: #FF7B72; color: #000'
            elif val == "BENIGN":
                return 'background-color: #3FB950; color: #000'
            return ''
        
        st.dataframe(df.style.map(style_verdict, subset=['Verdict']), use_container_width=True)
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Scan Log (CSV)", 
            data=csv, 
            file_name="quantum_security_scan_history.csv", 
            mime="text/csv",
            type="primary"
        )

def main():
    st.sidebar.title("🛡️ Threat Intelligence")
    st.sidebar.markdown("---")
    
    # Load backend singleton
    try:
        scanner = get_scanner()
    except Exception as e:
        st.error(f"Failed to load scanning modules: {e}")
        st.stop()
        
    # App Navigation
    page = st.sidebar.radio("Navigation", ["File Scanner", "Domain Scanner", "Scan History"])
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Quantum-Enhanced Threat Intelligence Dashboard**
    - Utilizes Ensemble Classical Random Forest.
    - Automatic fallbacks to Quantum SV Classifier on low confidence inputs.
    """)
    
    if page == "File Scanner":
        render_file_scanner(scanner)
    elif page == "Domain Scanner":
        render_domain_scanner(scanner)
    else:
        render_history()

if __name__ == "__main__":
    main()
