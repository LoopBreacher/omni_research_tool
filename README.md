# Omni Research Tool

The **Omni Research Tool** is an interactive, Python-based Streamlit application designed for gravitational-wave researchers, physicists, and enthusiasts. It bridges the gap between observational astrophysics and the theoretical **Universal Omni Framework**, providing an intuitive environment to instantly compare real black hole mergers from the LIGO/Virgo/KAGRA catalog against theoretical Quasinormal Mode (QNM) ringdown predictions.

## Features

- **Dynamic Catalog Integration:** Leverages the `gwosc` and `gwpy` libraries to fetch open-access strain data from hundreds of events across the full GWTC-4.0 catalog.
- **Smart Parameter Auto-Population:** Automatically retrieves and loads the canonical source-frame Final Mass ($M_f$) and Final Spin ($a_f$) for your chosen gravitational-wave event directly from GWOSC metadata.
- **Detector-Specific Targeting:** Allows you to extract specific strain timelines recorded by the Hanford (H1), Livingston (L1), or Virgo (V1) interferometers.
- **Time and Frequency Domain Analysis:** Visually compares theoretical Omni ringdowns (the "Acoustic Heartbeat") against raw interference data in the time domain, alongside deep frequency power spectrum mapping in the frequency domain. 
- **Theoretical Metrics Engine:** Evaluates framework-specific variables such as the Reality Ratio ($R$), Gamma Decay metrics, and theoretical Bekenstein Bounds against a universal $\Omega$ (OMEGA) constant.
- **Context-Aware Exports:** Seamlessly extract your analysis data. Every table, frequency spectrum, and waveform plot can be instantly exported locally with dynamically generated prefixes matching your targeted event (e.g., `GW150914_qnm_frequencies.csv`).

## Installation

Ensure you have Python 3.8+ installed. You can install all necessary dependencies by cloning the repository and running:

```bash
pip install -r requirements.txt
```

*Key dependencies include: `streamlit`, `numpy`, `pandas`, `plotly`, `gwosc`, and `gwpy`.*

## Usage

To launch the interactive Streamlit server locally, navigate to the project directory and run:

```bash
python -m streamlit run streamlit_app.py
```

You can interact with the app in your browser (typically at `http://localhost:8501`). Simply select an event and a detector from the sidebar, click the **Fetch Event Data** button, and explore the generated theoretical models.

## Pro-Tips & Troubleshooting

- **API Latency:** Fetching raw strain data directly from the GWOSC servers can sometimes take a few moments depending on network conditions.
- **Manual Parameter Lookup:** If the "Final Mass" or "Final Spin" sliders do not auto-populate for a specific event (or if you want to verify the best "Detector" for that event), you can look up the canonical catalog values directly at the [GWOSC Event API](https://gwosc.org/eventapi/html/GWTC/).
- **Missing Final Spin:** Note that for some entries in the physical catalog, the "Final Spin" parameter may be missing or undefined. This is a limitation of the available observational data and not an error within the Research Tool. In these cases, the tool defaults to a stable seed value.
- **Detector Availability:** Not every event is available on all three detectors (H1, L1, V1). Check the GWOSC site if a specific fetch returns an error.

## Theory & Context

This tool uses the generalized stability mechanics detailed in the **Universal Omni Equation**, an alternative theoretical approach evaluating the intersection of black hole ringdowns, QNM frequency damping, and macroscopic thermodynamic entropy.

### References

- **Read the foundational paper on OSF:** [Universal Omni Framework Paper](https://osf.io/dexp4/files/73j2c)
- **Visit the core GitHub Repository:** [Universal Omni Equation](https://github.com/LoopBreacher/Universal_Omni_Equation)

---
*Developed for the Universal Omni Framework by Marco Lindenbeck.*