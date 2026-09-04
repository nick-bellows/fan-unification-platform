# Mock Salesforce API only — deliberately does NOT install the full pipeline
# dependency set (pandas/splink/prefect). The app imports nothing outside
# fastapi/pydantic/stdlib; installing the project with --no-deps keeps the
# image small and honest about what the service needs.
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

WORKDIR /app

RUN pip install --no-cache-dir "fastapi>=0.111" "uvicorn>=0.30" \
    "pydantic>=2.7" "pydantic-settings>=2.3" "python-multipart>=0.0.9"

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8001
# Non-root runtime: the service only reads a mounted data dir.
USER nobody
CMD ["uvicorn", "fanuni.salesforce_mock.app:app", "--host", "0.0.0.0", "--port", "8001"]
