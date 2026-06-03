# ─────────────────────────────────────────────────────────────────────────────
# dMRI Rosetta Stone — FSL + MRtrix3 + DIPY + Streamlit
#
# --platform linux/amd64 is required on Apple Silicon (M1/M2/M3) because
# FSL and MRtrix3 conda packages are only built for x86_64 Linux.
# Docker Desktop handles the emulation transparently.
#
# Local build & test:
#   docker build --platform linux/amd64 -t dmri-rosetta .
#   docker run --platform linux/amd64 -p 8501:7860 dmri-rosetta
#   open http://localhost:8501
#
# HuggingFace Spaces: push the repo — HF builds on linux/amd64 automatically
# ─────────────────────────────────────────────────────────────────────────────

FROM --platform=linux/amd64 continuumio/miniconda3:24.1.2-0

# ── 1. System libraries ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        bc \
        dc \
        file \
        curl \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libgomp1 \
        libquadmath0 \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

# ── 2. Install mamba for faster solving ───────────────────────────────────────
RUN conda install -y -n base -c conda-forge mamba \
    && conda clean -afy

# ── 3. FSL core tools via the official FSL conda channel ─────────────────────
# Only the tools the app actually calls — avoids pulling the full 5 GB FSL
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

# FSL environment variables
ENV FSLDIR=/opt/conda
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH="${FSLDIR}/bin:${PATH}"

# ── 4. MRtrix3 ────────────────────────────────────────────────────────────────
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

# ── 6. Copy the app ───────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

# ── 7. Generate synthetic demo data at build time ─────────────────────────────
RUN python scripts/make_test_data.py --subject 100307 --outdir data/hcp

# ── 8. Runtime config ─────────────────────────────────────────────────────────
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

CMD ["streamlit", "run", "app/app.py", "--server.port=7860"]
