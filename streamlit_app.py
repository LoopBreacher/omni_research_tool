import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import csv
from io import BytesIO

# Try to import GWOSC and GWPY, display error gracefully if failing
try:
    from gwosc.datasets import event_gps
    from gwpy.timeseries import TimeSeries
    HAS_GWPY = True
except ImportError:
    HAS_GWPY = False

# Import from omni_core
from omni_core import compute_omni_qnm_waveform, get_qnm_table, OMEGA, M_REF, F0_REF, TAU0_REF

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Omni Research Tool",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CACHED DATA FETCHING ---
@st.cache_data(show_spinner=False)
def fetch_event_data_cached(event_name, detector="H1", show_full_signal=False):
    """Fetches real GW data + published remnant parameters from GWOSC for any detector."""
    if not HAS_GWPY:
        return None, None, 61.5, 0.68, "gwpy/gwosc not installed"
    
    try:
        gps = event_gps(event_name)
        
        # Use selected detector
        data = TimeSeries.fetch_open_data(detector, gps - 1.0, gps + 1.0)
        data = data.bandpass(35, 350)
        
        # Get published parameters from catalog
        try:
            params = gwosc.datasets.get_event_parameters(event_name)
        except Exception:
            try:
                import gwosc.api
                _ev_json = gwosc.api.fetch_event_json(event_name)
                pe_dicts = list(_ev_json['events'].values())[0]['parameters']
                params = list(pe_dicts.values())[0] if pe_dicts else {}
            except Exception:
                params = {}
                
        # Correct keys according to GWOSC API
        M_f = params.get('final_mass_source', 61.5)
        a_f = params.get('final_spin', params.get('chi_eff', 0.68))
        
        # Pure ringdown crop (t=0 at merger)
        t0 = gps
        if show_full_signal:
            data_crop = data.crop(t0 - 0.2, t0 + 0.06)
        else:
            data_crop = data.crop(t0, t0 + 0.06)
        
        t_s = data_crop.times.value - t0
        h_s = data_crop.value
        
        return t_s, h_s, float(M_f), float(a_f), None
    except Exception as e:
        return None, None, 61.5, 0.68, str(e)


def main():
    st.title("Omni Research Tool – Universal Omni Framework Predictions for Gravitational Waves")
    st.markdown("Analyze real gravitational-wave events against theoretical Quasinormal Mode (QNM) predictions from the Universal Omni Equation.")

    # --- SIDEBAR ---
    st.sidebar.header("Data Source")
    
    # Dynamic full GWTC-4.0 catalog (sorted by name)
    try:
        import gwosc.datasets
        event_list = sorted(gwosc.datasets.get_event_list(catalog="GWTC-4.0"))
    except Exception:
        import gwosc.datasets
        try:
            event_list = sorted(list(set([x.split('-')[0] for x in gwosc.datasets.find_datasets(type='events') if x.startswith('GW')])))
        except:
            event_list = ["GW150914", "GW151226", "GW170104", "GW170814", "GW190521"]
    selected_event = st.sidebar.selectbox("Select GW Event (GWTC-4.0):", event_list)
    
    # Detector selector
    detector_options = ["H1", "L1", "V1"]
    selected_detector = st.sidebar.selectbox("Select Detector:", detector_options, index=0)
    
    fetch_btn = st.sidebar.button("Fetch Event Data")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Alternative:**")
    uploaded_file = st.sidebar.file_uploader("Upload custom strain data (CSV)", type=["csv"])
    
    # --- DATA LOADING STATE ---
    # Store fetched data in session state
    if "t_ligo" not in st.session_state:
        st.session_state.t_ligo = None
        st.session_state.h_ligo = None
    if "event_params" not in st.session_state:
        st.session_state.event_params = {}

    st.sidebar.markdown("---")
    st.sidebar.header("Omni Model Parameters")
    
    # Auto-fill sliders with real event parameters (if available)
    default_mf = st.session_state.event_params.get(selected_event, {}).get("M_f", 61.5)
    default_af = st.session_state.event_params.get(selected_event, {}).get("a_f", 0.68)
    
    # Dynamic sliders for the model
    M_f = st.sidebar.slider("Final Mass ($M_f$) [M_sun]", min_value=10.0, max_value=300.0, value=float(default_mf), step=0.1)
    a_f = st.sidebar.slider("Final Spin ($a_f$)", min_value=0.00, max_value=0.99, value=float(default_af), step=0.01)

    show_full_signal = st.sidebar.checkbox("Show full signal (incl. late inspiral + merger)", value=False)

    if fetch_btn:
        with st.spinner(f"Fetching {selected_event} data from GWOSC..."):
            t_data, h_data, M_f_real, a_f_real, err = fetch_event_data_cached(selected_event, selected_detector, show_full_signal)
            if err:
                st.sidebar.error(f"Error fetching data: {err}")
            else:
                # Auto-update sliders with real catalog values
                M_f = M_f_real
                a_f = a_f_real
                st.session_state.t_ligo = t_data
                st.session_state.h_ligo = h_data
                st.session_state.event_params[selected_event] = {"M_f": M_f_real, "a_f": a_f_real}
                st.sidebar.success(f"Loaded {selected_event} — M_f={M_f:.1f} M☉, a_f={a_f:.2f}")
                st.rerun()  # Forces a rerun so the newly loaded parameters instantly update the sliders above
                
    # If user uploads a file, it overrides the fetched data
    if uploaded_file is not None:
        try:
            df_custom = pd.read_csv(uploaded_file)
            st.session_state.t_ligo = df_custom.iloc[:, 0].values
            st.session_state.h_ligo = df_custom.iloc[:, 1].values
            st.sidebar.success("Custom CSV loaded!")
        except Exception as e:
            st.sidebar.error("Error reading CSV. Need time, strain cols.")

    # --- CORE CALCULATION ---
    # Omni framework model
    t_omni, h_omni, f0, tau0 = compute_omni_qnm_waveform(M_f=M_f, a_f=a_f)
    
    # Normalizing LIGO data solely for shape visualization
    h_ligo_plot = None
    t_ligo_plot = None
    if st.session_state.h_ligo is not None:
        t_ligo_plot = st.session_state.t_ligo
        h_orig = st.session_state.h_ligo
        peak_omni = np.max(np.abs(h_omni))
        peak_ligo = np.max(np.abs(h_orig))
        if peak_ligo > 0:
            h_ligo_plot = h_orig * (peak_omni / peak_ligo)
        else:
            h_ligo_plot = h_orig

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Waveform Comparison", 
        "Frequency Spectrum", 
        "QNM Table", 
        "Stability Metrics", 
        "Export"
    ])

    with tab1:
        st.info("**Omni Framework** = pure theoretical ringdown (clean exponential damping from acoustic heartbeat + forgetting). "
                "**Actual LIGO data** = ringdown + detector noise + possible residual merger signal.")
        st.subheader("Time-Domain Waveform Ringdown")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=t_omni*1000.0, y=h_omni, 
            mode='lines', name='Omni Framework Prediction', 
            line=dict(color='blue', width=2)
        ))
        
        if h_ligo_plot is not None:
            fig1.add_trace(go.Scatter(
                x=t_ligo_plot*1000.0, y=h_ligo_plot, 
                mode='lines', name='Actual Data (Scaled)', 
                line=dict(color='black', width=1.5, dash='dash')
            ))
            
        fig1.update_layout(
            xaxis_title="Time (ms)", 
            yaxis_title="Strain (Normalized)",
            template="plotly_dark" if st.get_option("theme.base") != "light" else "plotly_white",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig1, width='stretch', config={
            'toImageButtonOptions': {
                'filename': f'{selected_event}_waveform'
            }
        })

    with tab2:
        st.subheader("Frequency Power Spectrum")
        
        # Calculate FFT for Omni
        N_o = len(t_omni)
        dt_o = t_omni[1] - t_omni[0]
        yf_o = np.fft.fft(h_omni)
        xf_o = np.fft.fftfreq(N_o, dt_o)[:N_o//2]
        power_o = 2.0 / N_o * np.abs(yf_o[0:N_o//2])

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=xf_o, y=power_o, 
            mode='lines', name='Omni Power Spectrum', 
            line=dict(color='red', width=2)
        ))
        
        # Calculate FFT for LIGO (if available)
        if h_ligo_plot is not None:
            N_l = len(t_ligo_plot)
            dt_l = t_ligo_plot[1] - t_ligo_plot[0]
            yf_l = np.fft.fft(h_ligo_plot)
            xf_l = np.fft.fftfreq(N_l, dt_l)[:N_l//2]
            power_l = 2.0 / N_l * np.abs(yf_l[0:N_l//2])
            
            fig2.add_trace(go.Scatter(
                x=xf_l, y=power_l, 
                mode='lines', name='Actual Data Spectrum', 
                line=dict(color='gray', width=1.5, dash='dot')
            ))
        
        # Annotate highest mode
        fig2.add_vline(x=f0, line_width=1, line_dash="dash", line_color="green", annotation_text=f"f0 = {f0:.1f} Hz")
        fig2.update_layout(
            xaxis_title="Frequency (Hz)", 
            yaxis_title="Power",
            xaxis_range=[0, 800],
            template="plotly_dark",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig2, width='stretch', config={
            'toImageButtonOptions': {
                'filename': f'{selected_event}_spectrum'
            }
        })

    with tab3:
        st.subheader("Quasinormal Mode (QNM) Frequencies")
        qnm_data = get_qnm_table(M_f=M_f, a_f=a_f)
        df_qnm = pd.DataFrame(qnm_data)
        st.dataframe(df_qnm, width='stretch', hide_index=True)
        
        csv_qnm = df_qnm.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download QNM Table (CSV)",
            data=csv_qnm,
            file_name=f"{selected_event}_qnm_frequencies.csv",
            mime="text/csv",
        )

    with tab4:
        st.subheader("Equation Stability Metrics")
        col1, col2, col3 = st.columns(3)
        
        # Derive basic thematic metrics based on the variables provided
        reality_ratio = (M_f / M_REF) * (1.0 - a_f) + 0.5
        s_base = 4.0 * np.pi * (M_f**2)
        gamma = tau0 / TAU0_REF
        
        col1.metric("Reality Ratio (R)", f"{reality_ratio:.4f}", "Optimal ~ 1.0")
        col2.metric("S_max (Bekenstein)", f"{s_base:.2e}", f"rel to OMEGA")
        col3.metric("Gamma Decay Ratio", f"γ ≈ {gamma:.3f}", "Acoustic Heartbeat scale")
        
        st.info(f"**OMEGA Constant used:** {OMEGA}")

    with tab5:
        st.subheader("Export Center")
        st.write("Download the resulting Omni generated data to CSV.")
        
        df_export = pd.DataFrame({
            "Time (s)": t_omni,
            "Strain_h": h_omni
        })
        csv_buffer = df_export.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="Download Predictions (CSV)",
            data=csv_buffer,
            file_name=f"{selected_event}_omni_qnm_prediction.csv",
            mime="text/csv",
        )
        st.write("*Note: To export charts as PNG, click the camera icon 'Download plot as a png' in the top right corner of any plot.*")

    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: grey; font-size: small;'>"
        "Universal Omni Framework by Marco Lindenbeck - 2026 | "
        "<a href='https://osf.io/dexp4/files/73j2c' style='color: #4da6ff;'>Paper (OSF)</a> | "
        "<a href='https://github.com/LoopBreacher/Universal_Omni_Equation' style='color: #4da6ff;'>GitHub Repository</a>"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
