FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libsdl2-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project

COPY triple_triad/ ./triple_triad/
COPY LICENSE README.md ./
RUN uv sync --no-dev
RUN uv pip install --system debugpy>=1.8.0

ENV PYTHONIOENCODING=utf-8
ENV SDL_VIDEODRIVER=dummy
ENV SDL_AUDIODRIVER=dummy

ENTRYPOINT ["uv", "run", "python", "-m", "triple_triad"]
