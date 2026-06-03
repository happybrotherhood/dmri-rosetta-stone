# ─────────────────────────────────────────────────────────────────────────────
# dMRI Rosetta Stone — FSL + MRtrix3 + DIPY + Streamlit
#
# Multi-stage build:
#   Stage 1 (mrtrix3)  → official MRtrix3 image, find where binaries live
#   Stage 2 (final)    → brainlife/fsl base + copy MRtrix3 bins + Python
#
# No conda for MRtrix3 — copy pre-built binaries from the official image.
#
# Build:  docker build --platform linux/amd64 -t dmri-rosetta .
# Run:    docker run  --platform linux/amd64 -p 8501:7860 dmri-rosetta
# Open:   http://localhost:8501
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: MRtrix3 source ───────────────────────────────────────────────────
FROM mrtrix3/mrtrix3:latest AS mrtrix3_stage

# ── Stage 2: Final image ──────────────────────────────────────────────────────
FROM brainlife/fsl:6.0.7.22

# FSL is pre-installed at /usr/local/fsl with FSLDIR and PATH already set

# ── 1. Copy MRtrix3 binaries from official image ──────────────────────────────
COPY --from=mrtrix3_stage /mrtrix3 /opt/mrtrix3
ENV PATH="/opt/mrtrix3/bin:${PATH}"

# ── 2. System packages the app needs ─────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        wget \
        python3-pip \
        libgl1-mesa-glx \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── 3. Python packages ────────────────────────────────────────────────────────
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

# ── 4. App ────────────────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

RUN python3 scripts/make_test_data.py --subject 100307 --outdir data/hcp

# ── 5. Runtime ────────────────────────────────────────────────────────────────
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

CMD ["streamlit", "run", "app/app.py", "--server.port=7860"]
