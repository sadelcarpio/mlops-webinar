# Imagen de producción: la Lambda, con solo lo necesario (versiones fijadas por uv.lock)
FROM public.ecr.aws/lambda/python:3.12 AS produccion
COPY --from=ghcr.io/astral-sh/uv:0.8.18 /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt \
 && uv pip install --system --no-cache -r requirements.txt
COPY pipeline/ pipeline/
CMD ["pipeline.aws.handler"]

# Imagen de tests: la MISMA imagen de producción + pytest/ruff + los tests
FROM produccion AS tests
RUN uv export --frozen --only-group test --no-emit-project --no-hashes -o requirements-test.txt \
 && uv pip install --system --no-cache -r requirements-test.txt
COPY tests/ tests/
ENTRYPOINT []
CMD ["sh", "-c", "ruff check pipeline tests && python -m pytest -v"]
