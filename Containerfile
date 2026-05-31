ARG PYTHON_VERSION=3.14.4-slim-trixie

FROM docker.io/library/python:${PYTHON_VERSION} AS base

# Set environment variables for Python, Pip, Poetry and project directories
# PYTHONUNBUFFERED=1 --> Forces immediate output to the terminal/logs. 
# PYTHONDONTWRITEBYTECODE=1 --> Prevents the creation of .pyc files. 
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PROJECT_DIR="/adeeb_fastapi"

    # Add Poetry to the PATH
ENV PATH="$POETRY_HOME/bin:$PROJECT_DIR/.venv/bin:$PATH"

# Set working directory for all stages.
WORKDIR $PROJECT_DIR

# Install system dependencies
RUN buildDeps="build-essential" \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    && apt-get install -y --no-install-recommends $buildDeps \
    && rm -rf /var/lib/apt/lists/*


################################################################################
FROM base AS deps

# Set Poetry version
ENV POETRY_VERSION=2.3.4

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python3 - && chmod a+x /opt/poetry/bin/poetry

RUN python -m venv .venv

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage bind mounts to pyproject.toml and package-lock.json to avoid having to copy them
# Install package dependencies with poetry, 
# COPY poetry.lock pyproject.toml ./
RUN --mount=type=bind,source=poetry.lock,target=poetry.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    poetry env use .venv/bin/python3

# use --no-root because we didn't copy adeeb_fastapi/adeeb_fastapi yet
RUN --mount=type=bind,source=poetry.lock,target=poetry.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    poetry install --no-root

################################################################################
FROM deps as build

# Set working directory and copy package files
COPY . .

EXPOSE 8000

# Use, if you'll run the Container directly
#
# Use if you use compose file, and seet default command to run the application there.
CMD [""]
