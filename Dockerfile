# ─────────────────────────────────────────────────────────────────────────────
# dMRI Rosetta Stone — FSL + MRtrix3 + DIPY + Streamlit
#
# Base: ubuntu:22.04  (always available, no auth needed)
# MRtrix3: copied from official mrtrix3/mrtrix3:latest image (stage 1)
# FSL: official fslinstaller.py script
#
# Build:  docker build --platform linux/amd64 -t dmri-rosetta .
# Run:    docker run  --platform linux/amd64 -p 8501:7860 dmri-rosetta
# Open:   http://localhost:8501
# ─────────────────────────────────────────────────────────────────────────────

# Global ARG — must be before all FROM statements to be usable in FROM --platform
# Default linux/amd64 because FSL only ships linux/amd64 binaries
ARG TARGETPLATFORM=linux/amd64

# ── Stage 1: grab MRtrix3 binaries from the official image ───────────────────
FROM mrtrix3/mrtrix3:latest AS mrtrix3_stage

# ── Stage 2: main image ───────────────────────────────────────────────────────
FROM --platform=${TARGETPLATFORM} ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/London

# ── 1. System packages ────────────────────────────────────────────────────────
# bzip2         : extracts micromamba .tar.bz2 during FSL install
# libxt6        : FSL runtime dependency
# libquadmath0  : FSL numerical libs
# python3-distutils : fslinstaller.py on Python 3.10 (Ubuntu 22.04)
# libfftw3-3 / libpng16-16 / libtiff5 : MRtrix3 runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        bc \
        binutils \
        bzip2 \
        curl \
        dc \
        file \
        libfftw3-3 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libgomp1 \
        libpng16-16 \
        libquadmath0 \
        libtiff5 \
        libxt6 \
        python3 \
        python3-distutils \
        python3-pip \
        wget \
    && rm -rf /var/lib/apt/lists/*

# ── 2. FSL via official installer script ─────────────────────────────────────
# fslinstaller.py handles download + install non-interactively
# -d : install directory
# --skip_registration : no interactive prompts
RUN wget -q https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py \
    && python3 fslinstaller.py -d /usr/local/fsl --skip_registration \
    && rm fslinstaller.py

ENV FSLDIR=/usr/local/fsl
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV FSLMULTIFILEQUIT=TRUE
ENV FSLTCLSH=/usr/local/fsl/bin/fsltclsh
ENV FSLWISH=/usr/local/fsl/bin/fslwish
ENV PATH="${FSLDIR}/bin:${PATH}"

# ── 3. MRtrix3 binaries from stage 1 ─────────────────────────────────────────
COPY --from=mrtrix3_stage /opt/mrtrix3 /opt/mrtrix3
ENV PATH="/opt/mrtrix3/bin:${PATH}"

# MRtrix3 is compiled against libtiff.so.6 but Ubuntu 22.04 only ships libtiff.so.5.
# The ABI is compatible — a symlink resolves the missing library at runtime.
RUN ln -sf /usr/lib/x86_64-linux-gnu/libtiff.so.5 \
           /usr/lib/x86_64-linux-gnu/libtiff.so.6

# ── 4. Python packages ────────────────────────────────────────────────────────
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

# ── 5. App ────────────────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

RUN python3 scripts/make_test_data.py --subject 100307 --outdir data/hcp

# ── 6. Runtime ────────────────────────────────────────────────────────────────
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

CMD ["streamlit", "run", "app/app.py", "--server.port=7860"]
