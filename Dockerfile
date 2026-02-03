FROM ghcr.io/astral-sh/uv:alpine

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

CMD ["sh", "-c", "uv run alembic upgrade head && uv run main.py"]