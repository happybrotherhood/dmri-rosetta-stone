#!/bin/bash
# Launch the dMRI Rosetta Stone Streamlit app using Python 3.10 env
PYTHON=/Users/Busra/opt/anaconda3/envs/pythonProject/bin/python
cd "$(dirname "$0")"
$PYTHON -m streamlit run app/app.py --server.port 8501
