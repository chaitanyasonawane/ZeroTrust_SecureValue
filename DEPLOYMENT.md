# Final Deployment Guide

## macOS

1. Open Terminal.
2. Move into this folder:
   `cd /path/to/ZeroTrust_Final_Deployment`
3. Run:
   `./run_mac.sh`

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will display a local address, normally:
`http://localhost:8501`

## Windows

Double-click `run_windows.bat`, or run:
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Before the thesis demonstration

- Use documented risk probabilities and financial impacts.
- Record the source/justification for each input.
- Do not present demonstration values as empirical findings.
- Keep the prototype offline/local unless a later deployment requirement is given.
