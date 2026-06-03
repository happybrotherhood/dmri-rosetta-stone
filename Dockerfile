# dMRI Rosetta Stone — Docker image with FSL + MRtrix3 + DIPY
#
# Build:  docker build -t dmri-rosetta-stone .
# Run:    docker run -p 8501:8501 dmri-rosetta-stone
#
# For HuggingFace Spaces: port must be 7860

FROM continuumio/miniconda3:24.1.2-0

# ── System deps ───────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    dc \
    wget \
    git \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ── Conda environment ─────────────────────────────────────────────────────────
# Install FSL core tools via FSL's official conda channel (FSL 6.0.7+)
# We only install the tools the app actually uses — avoids pulling 5 GB of FSL
RUN conda install -y -c conda-forge -c https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/ \
    fsl-avwutils \
    fsl-bet2 \
    fsl-dtifit \
    fsl-fast \
    fsl-flirt \
    fsl-fnirt \
    fsl-tbss \
    fsl-randomise \
    && conda clean -afy

# Install MRtrix3 via conda
RUN conda install -y -c mrtrix3 mrtrix3 \
    && conda clean -afy

# ── FSL environment variables ─────────────────────────────────────────────────
ENV FSLDIR=/opt/conda
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH="${FSLDIR}/bin:${PATH}"

# ── Python packages ───────────────────────────────────────────────────────────
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
    streamlit>=1.40 \
    nibabel>=5.0 \
    numpy>=1.24 \
    scipy>=1.10 \
    matplotlib>=3.7 \
    pandas>=2.0 \
    networkx>=3.0 \
    dipy

# ── App ───────────────────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

# Pre-generate synthetic demo data so the app starts immediately
RUN python scripts/make_test_data.py --subject 100307 --outdir data/hcp

# HuggingFace Spaces requires port 7860
EXPOSE 7860

CMD ["streamlit", "run", "app/app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
