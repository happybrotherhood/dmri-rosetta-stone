# ─────────────────────────────────────────────────────────────────────────────
# dMRI Rosetta Stone
# FSL + MRtrix3 + DIPY + Streamlit in one container
#
# Local test:
#   docker build -t dmri-rosetta .
#   docker run -p 8501:7860 dmri-rosetta
#   open http://localhost:8501
#
# HuggingFace Spaces: push this repo → HF builds automatically (port 7860)
# ─────────────────────────────────────────────────────────────────────────────

FROM continuumio/miniconda3:24.1.2-0

# ── 1. System libraries that FSL/MRtrix3 need ─────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        bc \
        dc \
        file \
        libfftw3-dev \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libgomp1 \
        liblapack-dev \
        wget \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

# ── 2. Speed up conda with mamba ──────────────────────────────────────────────
RUN conda install -y -n base -c conda-forge mamba \
    && conda clean -afy

# ── 3. FSL — via the official FSL conda channel ───────────────────────────────
# Installing only the tools the app actually calls (saves ~3 GB vs full FSL)
RUN mamba install -y \
        -c https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/ \
        -c conda-forge \
        fsl-avwutils \
        fsl-bet2 \
        fsl-dtifit \
        fsl-eddy \
        fsl-fast \
        fsl-flirt \
        fsl-fnirt \
        fsl-topup \
        fsl-tbss \
        fsl-randomise \
    && conda clean -afy

# FSL environment
ENV FSLDIR=/opt/conda
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH="${FSLDIR}/bin:${PATH}"

# ── 4. MRtrix3 — via the official mrtrix3 conda channel ──────────────────────
RUN mamba install -y \
        -c mrtrix3 \
        -c conda-forge \
        mrtrix3 \
    && conda clean -afy

# ── 5. Python packages ────────────────────────────────────────────────────────
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

# ── 6. Copy app ───────────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

# ── 7. Pre-generate synthetic demo data ───────────────────────────────────────
# So the app starts immediately without any user setup
RUN python scripts/make_test_data.py --subject 100307 --outdir data/hcp

# ── 8. Streamlit config ───────────────────────────────────────────────────────
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# HuggingFace Spaces uses port 7860
# For local testing: docker run -p 8501:7860 dmri-rosetta
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -f http://localhost:7860 || exit 1

CMD ["streamlit", "run", "app/app.py", "--server.port=7860"]
