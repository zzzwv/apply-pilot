ARG BACKEND_BASE_IMAGE=python:3.12-slim
FROM ${BACKEND_BASE_IMAGE}
ARG SKIP_DEPENDENCY_INSTALL=false
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts
COPY alembic.ini ./
COPY alembic ./alembic
RUN if [ "$SKIP_DEPENDENCY_INSTALL" != "true" ]; then pip install --no-cache-dir .; fi
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
