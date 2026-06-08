ARG PYTHON_VERSION=3.14.4-slim-trixie

FROM docker.io/library/python:${PYTHON_VERSION} AS base

# Set environment variables for Python, Pip, Poetry and project directories
# PYTHONUNBUFFERED=1 --> Forces immediate output to the terminal/logs. 
# PYTHONDONTWRITEBYTECODE=1 --> Prevents the creation of .pyc files. 
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PDM_CHECK_UPDATE=false \
    PDM_CACHE_DIR=/tmp/pdm-cache \
    PDM_CHECK_UPDATE=false \
    PDM_NON_INTERACTIVE=true \
    PDM_HOME="/opt/pdm" \
    PROJECT_DIR="/adeeb_fastapi"

    

# Add Poetry to the PATH
ENV PATH="$PDM_HOME/bin:$PROJECT_DIR/.venv/bin:$PATH"

# Set working directory for all stages.
WORKDIR $PROJECT_DIR


################################################################################
FROM base AS deps


# Set Poetry version
ENV PDM_VERSION=2.27.0

# Install PDM - respects $PDM_VERSION & $PDM_HOME
RUN pip install --no-cache-dir pdm==$PDM_VERSION


RUN python -m venv .venv

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage bind mounts to pyproject.toml and package-lock.json to avoid having to copy them
# Install package dependencies with pdm, 
# COPY pdm.lock pyproject.toml ./
RUN --mount=type=bind,source=pdm.lock,target=pdm.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    mkdir __pypackages__ && pdm sync --prod --no-editable


################################################################################
FROM deps as build

# Set working directory and copy package files
COPY . .

EXPOSE 8000

# Use, if you'll run the Container directly
#CMD ["pdm", "run", "uvicorn", "adeeb_fastapi.main:app", "--port", "8000"]
# Use if you use compose file, and seet default command to run the application there.
CMD [""]
