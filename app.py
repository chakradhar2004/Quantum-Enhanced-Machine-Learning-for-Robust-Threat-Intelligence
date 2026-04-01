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
    page_title="ThreatIntel | Quantum Core",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark cybersecurity theme custom CSS
st.markdown("""
<style>
    /* Dark Theme Setup */
    .stApp {
        background-color: #0a0f1c;
        color: #e2e8f0;
    }
    
    /* Typography */
    * {
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
    }

    /* Cyber Typography */
    .cyber-header {
        background: linear-gradient(90deg, #00f7ff 0%, #0066ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 2.8rem;
        letter-spacing: -1px;
        margin-bottom: 0.2rem;
        text-shadow: 0 0 30px rgba(0, 247, 255, 0.2);
    }
    .cyber-subtitle {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #050812 !important;
        border-right: 1px solid #1e293b;
    }

    /* Custom Cards */
    .cyber-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
        height: 100%;
    }
    .cyber-card:hover {
        border-color: #00f7ff;
        box-shadow: 0 0 20px rgba(0, 247, 255, 0.1);
        transform: translateY(-2px);
    }
    .cyber-card-title {
        color: #64748b;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .cyber-card-value {
        color: #f8fafc;
        font-size: 1.5rem;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-family: 'JetBrains Mono', Consolas, monospace;
    }

    /* Verdict Specific Styling */
    .verdict-malicious {
        color: #ff4b4b !important;
        text-shadow: 0 0 15px rgba(255, 75, 75, 0.4);
    }
    .verdict-benign {
        color: #00ff9f !important;
        text-shadow: 0 0 15px rgba(0, 255, 159, 0.4);
    }
    .verdict-suspicious {
        color: #ffaa00 !important;
        text-shadow: 0 0 15px rgba(255, 170, 0, 0.4);
    }

    /* Quantum Animation Container */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 10px rgba(0, 247, 255, 0.1); border-color: #1e293b; }
        50% { box-shadow: 0 0 25px rgba(0, 247, 255, 0.4); border-color: #00f7ff; }
        100% { box-shadow: 0 0 10px rgba(0, 247, 255, 0.1); border-color: #1e293b; }
    }
    .quantum-active {
        animation: pulseGlow 3s infinite;
        background: linear-gradient(180deg, rgba(15, 23, 42, 1) 0%, rgba(0, 30, 40, 1) 100%);
        border-left: 4px solid #00f7ff;
    }

    /* Streamlit Uploader Overrides */
    [data-testid="stFileUploader"] > div > div {
        background-color: #0f172a !important;
        border: 1px dashed #334155 !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploader"] > div > div:hover {
        border-color: #00f7ff !important;
    }

    /* Primary Button Overrides */
    button[kind="primary"] {
        background: linear-gradient(90deg, #00f7ff 0%, #0066ff 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
        padding: 0.5rem 2rem !important;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 0 20px rgba(0, 247, 255, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Text Input */
    div[data-baseweb="input"] > div {
        background-color: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 6px;
    }
    div[data-baseweb="input"] > div:focus-within {
        border-color: #00f7ff !important;
        box-shadow: 0 0 0 1px #00f7ff !important;
    }
    
    /* Code blocks / json */
    .stCodeBlock {
        background-color: #050812 !important;
        border: 1px solid #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Initializing AI Models...")
def get_scanner():
    """Load the models once using ThreatScanner backend to handle caching"""
    vt_key = os.environ.get("VT_API_KEY", None)
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

def render_metric_card(title, value, verdict_class=""):
    """Helper functional to render styled cards"""
    st.markdown(f"""
        <div class="cyber-card">
            <div class="cyber-card-title">{title}</div>
            <div class="cyber-card-value {verdict_class}">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def render_quantum_alert():
    st.markdown("""
        <div class="cyber-card quantum-active" style="padding: 15px 20px; display: flex; align-items: center; gap: 15px; margin-bottom: 25px;">
            <div style="font-size: 2rem; color: #00f7ff; text-shadow: 0 0 10px #00f7ff;">⚛️</div>
            <div>
                <div style="color: #00f7ff; font-weight: 700; font-size: 1.1rem; letter-spacing: 1px;">QUANTUM FALLBACK ENGAGED</div>
                <div style="color: #94a3b8; font-size: 0.9rem;">Classical limits reached. Re-routing analysis to Quantum Support Vector Classifier (QSVC).</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def get_verdict_style(verdict):
    if verdict == "MALICIOUS": return "🚨 MALICIOUS", "verdict-malicious"
    if verdict == "BENIGN": return "✅ BENIGN", "verdict-benign"
    if verdict == "SUSPICIOUS": return "⚠️ SUSPICIOUS", "verdict-suspicious"
    return "❓ UNKNOWN", ""

def render_file_scanner(scanner):
    st.markdown('<div class="cyber-header">File Analysis Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="cyber-subtitle">Deep learning endpoint execution profiling</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload PE Payload (.exe, .dll, .bin)", type=['exe', 'dll', 'bin'])
    
    if uploaded_file is not None and st.button("Initialize Scan", type="primary", use_container_width=True):
        with st.spinner("Scanning with AI + Quantum engine..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name
            
            try:
                progress_container = st.empty()
                progress_bar = progress_container.progress(0, text="Hashing payload...")
                time.sleep(0.3)
                
                # 1. Run ML scan
                progress_bar.progress(35, text="Extracting structure traits...")
                results = scanner.file_scanner.scan_file(tmp_path)
                
                if 'error' in results:
                    st.error(f"Scan failed: {results['error']}")
                    return
                
                progress_bar.progress(65, text="Applying Classical Random Forest...")
                prediction = results.get('ml_prediction', 'UNKNOWN')
                confidence = results.get('ml_confidence', 0.0)
                
                model_used = "RF (Classical)"
                final_verdict = prediction
                final_confidence = confidence
                
                # Check for Quantum fallback
                if results.get('needs_quantum_analysis', False):
                    progress_bar.progress(80, text="Ambivalence detected. Booting QSVC...")
                    render_quantum_alert()
                    features = scanner.file_scanner.extract_pe_features(Path(tmp_path))
                    
                    if features is not None:
                        q_results = scanner.quantum_analyzer.analyze(features, method='qsvc')
                        model_used = "RF + QSVC (Ensemble)"
                        q_conf = q_results.get('confidence', q_results.get('quantum_confidence', 0.0))
                        
                        final_confidence = (confidence * 0.7) + (q_conf * 0.3)
                        
                        if final_confidence >= 0.7: final_verdict = "MALICIOUS"
                        elif final_confidence >= 0.5: final_verdict = "SUSPICIOUS"
                        else: final_verdict = "BENIGN"
                    else:
                        st.error("Quantum feature mismatch.")
                        
                progress_bar.progress(100, text="Analysis Complete.")
                time.sleep(0.5)
                progress_container.empty()
                
                # Render Dashboard Results
                st.markdown("### Threat Telemetry")
                
                col1, col2, col3 = st.columns(3)
                
                display_verdict, v_class = get_verdict_style(final_verdict)
                with col1: render_metric_card("Verdict", display_verdict, v_class)
                with col2: render_metric_card("Confidence", f"{final_confidence*100:.1f}%")
                with col3: render_metric_card("Engine", model_used)

                col4, col5 = st.columns([1, 2])
                with col4:
                    render_metric_card("Size", f"{results.get('file_size_mb', 0):.2f} MB")
                with col5:
                    sha256 = results.get('hashes', {}).get('sha256', 'N/A')
                    render_metric_card("SHA-256 Signature", sha256)
                
                log_scan("File", uploaded_file.name, final_verdict, final_confidence, model_used)
                
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except PermissionError:
                        pass


def render_domain_scanner(scanner):
    st.markdown('<div class="cyber-header">Domain Threat Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="cyber-subtitle">DGA Identification & Reputation Scanning</div>', unsafe_allow_html=True)
    
    domain_input = st.text_input("Deploy Target Domain", placeholder="e.g. suspicious-dga123.net")
    
    if st.button("Initiate Drone Scan", type="primary", use_container_width=True) and domain_input:
        with st.spinner("Scanning with AI + Quantum engine..."):
            progress_container = st.empty()
            progress_bar = progress_container.progress(0, text="Parsing domain structure...")
            time.sleep(0.3)
            
            progress_bar.progress(35, text="Applying Classical Random Forest...")
            results = scanner.domain_scanner.scan_domain(domain_input)
            
            prediction = results.get('ml_prediction', 'UNKNOWN')
            confidence = results.get('ml_confidence', 0.0)
            
            model_used = "RF (Classical)"
            final_verdict = prediction
            final_confidence = confidence
            
            if results.get('needs_quantum_analysis', False):
                progress_bar.progress(70, text="Ambivalence detected. Booting QSVC...")
                render_quantum_alert()
                try:
                    _, feature_dict = scanner.domain_scanner.extract_domain_features(domain_input)
                    if feature_dict is not None:
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
                            final_confidence = (confidence * 0.7) + (q_conf * 0.3)
                            
                            if final_confidence >= 0.7: final_verdict = "MALICIOUS"
                            elif final_confidence >= 0.5: final_verdict = "SUSPICIOUS"
                            else: final_verdict = "BENIGN"
                except Exception as e:
                    st.error(f"Quantum extraction error: {e}")
            
            progress_bar.progress(100, text="Analysis Complete.")
            time.sleep(0.5)
            progress_container.empty()
            
            st.markdown("### Threat Telemetry")
            col1, col2, col3 = st.columns(3)
            
            display_verdict, v_class = get_verdict_style(final_verdict)
            with col1: render_metric_card("Verdict", display_verdict, v_class)
            with col2: render_metric_card("Confidence", f"{final_confidence*100:.1f}%")
            with col3: render_metric_card("Engine", model_used)
            
            if 'features' in results:
                st.markdown("#### Dimensional Variables")
                with st.container():
                    f1, f2, f3, f4, f5 = st.columns(5)
                    fx = results['features']
                    with f1: render_metric_card("Length", f"{fx.get('length', 0)}")
                    with f2: render_metric_card("Entropy", f"{fx.get('entropy', 0):.2f}")
                    with f3: render_metric_card("Vowel Ratio", f"{fx.get('vowel_ratio', 0):.2f}")
                    with f4: render_metric_card("Digit Ratio", f"{fx.get('digit_ratio', 0):.2f}")
                    with f5: render_metric_card("Consonant Ratio", f"{fx.get('consonant_ratio', 0):.2f}")
                
            log_scan("Domain", domain_input, final_verdict, final_confidence, model_used)

def render_history():
    st.markdown('<div class="cyber-header">Operations Log</div>', unsafe_allow_html=True)
    st.markdown('<div class="cyber-subtitle">Session History & Audit Trail</div>', unsafe_allow_html=True)
    
    if not st.session_state.scan_history:
        st.info("No scanning operations logged in standard operational memory.")
    else:
        df = pd.DataFrame(st.session_state.scan_history)
        
        # Cyber styling for dataframe using pandas styler
        def background_style(val):
            if val == "MALICIOUS": return 'background-color: #ff4b4b; color: white; font-weight: bold;'
            if val == "BENIGN": return 'background-color: #00ff9f; color: black; font-weight: bold;'
            if val == "SUSPICIOUS": return 'background-color: #ffaa00; color: black; font-weight: bold;'
            return ''

        styled_df = df.style.map(background_style, subset=['Verdict']).set_properties(**{
            'background-color': '#0f172a',
            'color': '#f8fafc',
            'border-color': '#1e293b'
        })
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Immutable Log (CSV)", 
            data=csv, 
            file_name="ops_security_log.csv", 
            mime="text/csv",
            type="primary"
        )

def main():
    st.sidebar.markdown(
        '<div style="font-size: 24px; font-weight: 900; color: #00f7ff; margin-bottom: 2rem; letter-spacing: 2px;">⚡ THREAT_INTEL</div>', 
        unsafe_allow_html=True
    )
    
    try:
        scanner = get_scanner()
    except Exception as e:
        st.error(f"Failed to boot core modules: {e}")
        st.stop()
        
    page = st.sidebar.radio("COMMAND CENTER", ["File Scanner", "Domain Scanner", "Scan History"])
    
    st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
    st.sidebar.markdown("""
        <div style="padding: 15px; border: 1px solid #1e293b; border-radius: 8px; background-color: #0f172a;">
            <div style="color: #64748b; font-size: 0.8rem; text-transform: uppercase;">System Status</div>
            <div style="color: #00ff9f; font-weight: bold; margin-top: 5px;">⬤ CORES ONLINE</div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 10px;">Ensemble RF + VQC/QSVC Fallback Active.</div>
        </div>
    """, unsafe_allow_html=True)
    
    if page == "File Scanner":
        render_file_scanner(scanner)
    elif page == "Domain Scanner":
        render_domain_scanner(scanner)
    else:
        render_history()

if __name__ == "__main__":
    main()
