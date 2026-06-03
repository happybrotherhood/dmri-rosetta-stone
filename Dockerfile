# ─────────────────────────────────────────────────────────────────────────────
# dMRI Rosetta Stone — FSL + MRtrix3 + DIPY + Streamlit
#
# FSL  → NeuroDebian apt  (reliable, battle-tested)
# MRtrix3 → mrtrix3 conda channel
# DIPY → pip
#
# Build:  docker build --platform linux/amd64 -t dmri-rosetta .
# Run:    docker run  --platform linux/amd64 -p 8501:7860 dmri-rosetta
# Open:   http://localhost:8501
# ─────────────────────────────────────────────────────────────────────────────

FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/London

# ── 1. Core system packages ───────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        bc \
        curl \
        dc \
        file \
        gnupg2 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libgomp1 \
        python3 \
        python3-pip \
        wget \
    && rm -rf /var/lib/apt/lists/*

# ── 2. FSL via NeuroDebian ────────────────────────────────────────────────────
# NeuroDebian is the standard apt repository for neuroimaging tools on Debian/Ubuntu
RUN wget -q -O /etc/apt/sources.list.d/neurodebian.sources.list \
        http://neuro.debian.net/lists/jammy.us-nh.full \
    && wget -q -O- http://neuro.debian.net/_files/neurodebian-keyring.gpg \
        | apt-key add - \
    && apt-get update \
    && apt-get install -y --no-install-recommends fsl \
    && rm -rf /var/lib/apt/lists/*

# FSL environment — NeuroDebian installs to /usr/lib/fsl/<version>
ENV FSLDIR=/usr/share/fsl/6.0
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH="${FSLDIR}/bin:/usr/lib/fsl/6.0:${PATH}"
ENV LD_LIBRARY_PATH="/usr/lib/fsl/6.0:${LD_LIBRARY_PATH}"

# ── 3. Miniconda (for MRtrix3) ────────────────────────────────────────────────
RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh

ENV PATH="/opt/conda/bin:${PATH}"

# ── 4. MRtrix3 via conda ──────────────────────────────────────────────────────
RUN conda install -y -n base -c conda-forge mamba \
    && mamba install -y -c mrtrix3 -c conda-forge mrtrix3 \
    && conda clean -afy

# ── 5. Python packages ────────────────────────────────────────────────────────
RUN pip3 install --no-cache-dir \
        "streamlit>=1.40" \
        "nibabel>=5.0" \
        "numpy>=1.24,<2.0" \
        "scipy>=1.10" \
        "matplotlib>=3.7" \
        "pandas>=2.0" \
        "networkx>=3.0" \
        "dipy>=1.7" \
        "scikit-image>=0.20"

# ── 6. App ────────────────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

# Generate synthetic demo data so app starts immediately with no user setup
RUN python3 scripts/make_test_data.py --subject 100307 --outdir data/hcp

# ── 7. Runtime ────────────────────────────────────────────────────────────────
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

CMD ["streamlit", "run", "app/app.py", "--server.port=7860"]
