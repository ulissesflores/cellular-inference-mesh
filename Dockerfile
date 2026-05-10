# =============================================================================
# Cellular Inference Mesh — reproducible Docker image
# =============================================================================
# Purpose: containerize the Salabim discrete-event simulation so any machine
# can run `pytest` and the canonical 300-replicate Monte-Carlo with bit-identical
# outputs. The image pins Python to 3.14.4 to match `output/experiment_provenance.json`
# and `requirements.txt`.
#
# Base image rationale: python:3.14-slim is ~75 MB compressed (vs ~370 MB for
# python:3.14-bookworm) and includes a working glibc + ssl stack — sufficient
# for NumPy/SciPy wheels. The Apple Silicon and x86-64 multi-arch manifests
# from Docker Hub make this image portable across ARM64 macOS and amd64 Linux.
# =============================================================================

FROM python:3.14-slim

# OCI standard labels (https://github.com/opencontainers/image-spec).
LABEL org.opencontainers.image.title="cellular-inference-mesh"
LABEL org.opencontainers.image.description="Salabim discrete-event simulation of edge-cloud LLM inference under PACELC saturation"
LABEL org.opencontainers.image.authors="Carlos Ulisses Flores <c.ulisses@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/ulissesflores/cellular-inference-mesh"
LABEL org.opencontainers.image.documentation="https://github.com/ulissesflores/cellular-inference-mesh/tree/main/docs"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.version="0.3.0"

# git is needed at install time to support `pip install -e .` from VCS dependencies
# if any are added in the future. Removed from /var/lib/apt/lists/ to shave layer size.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------
# Layer ordering: dependencies installed BEFORE source copy so the
# requirements layer is cache-hit on most code edits. Bumping any
# package version invalidates this layer (intentional cache-bust).
# ---------------------------------------------------------------------
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source artifacts. The .dockerignore excludes output/, colab/, docs/,
# .venv/, __pycache__/, .pytest_cache/ to keep the image lean.
COPY src/ ./src/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY pyproject.toml CITATION.cff LICENSE README.md ./

# PYTHONUNBUFFERED ensures real-time stdout/stderr (no buffering), which is
# critical for `docker logs` to show progress during the ~31-min canonical run.
# PYTHONPATH lets `python -m src.main` resolve without requiring `pip install -e .`.
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Default: smoke test (~30 s) — confirms the image is healthy.
# To run the full canonical simulation (~31 min, 8 cores):
#   docker run --rm -v $(pwd)/output:/app/output \
#       cellular-inference-mesh:0.3.0 \
#       python -m src.main --replicates 300 --duration 1800 --workers 8
CMD ["python", "-m", "src.main", "--smoke"]
