#!/bin/bash
# Launch the dMRI Rosetta Stone Streamlit app locally.
# Usage: bash run_app.sh
set -e
cd "$(dirname "$0")"
python3 -m streamlit run app/app.py --server.port 8501
