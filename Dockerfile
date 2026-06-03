# ─────────────────────────────────────────────────────────────────────────────
# dMRI Rosetta Stone — FSL + MRtrix3 + DIPY + Streamlit
#
# Strategy: start from brainlife/fsl (FSL already installed + configured),
# add MRtrix3 via conda, add Python packages via pip.
# No package manager fights — FSL comes pre-baked.
#
# Build:  docker build --platform linux/amd64 -t dmri-rosetta .
# Run:    docker run  --platform linux/amd64 -p 8501:7860 dmri-rosetta
# Open:   http://localhost:8501
# ─────────────────────────────────────────────────────────────────────────────

FROM brainlife/fsl:6.0.7.22

# FSL is already installed at /usr/local/fsl
# FSLDIR, PATH, and FSLOUTPUTTYPE are already set in this image

# ── 1. Extra system packages ──────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        wget \
        libgl1-mesa-glx \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── 2. Miniconda (needed for MRtrix3) ────────────────────────────────────────
RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh

ENV PATH="/opt/conda/bin:${PATH}"

# ── 3. MRtrix3 ────────────────────────────────────────────────────────────────
RUN conda install -y -n base -c conda-forge mamba \
    && mamba install -y -c mrtrix3 -c conda-forge mrtrix3 \
    && conda clean -afy

# ── 4. Python packages ────────────────────────────────────────────────────────
RUN pip install --no-cache-dir \
        "streamlit>=1.40" \
        "nibabel>=5.0" \
        "numpy>=1.24,<2.0" \
        "scipy>=1.10" \
        "matplotlib>=3.7" \
        "pandas>=2.0" \
        "networkx>=3.0" \
        "dipy>=1.7" \
        "scikit-image>=0.20"

# ── 5. App ────────────────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

RUN python scripts/make_test_data.py --subject 100307 --outdir data/hcp

# ── 6. Runtime ────────────────────────────────────────────────────────────────
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

CMD ["streamlit", "run", "app/app.py", "--server.port=7860"]
