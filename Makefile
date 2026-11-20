# Uso: make test (igual que CI) · make test-rapido (sin Docker)
.PHONY: test test-rapido

test:  ## lint + tests DENTRO del contenedor, exactamente lo que corre GitHub Actions
	docker build --target tests -t demanda-tests .
	docker run --rm demanda-tests

test-rapido:  ## lint + tests en tu máquina, para iterar rápido
	uv run ruff check pipeline tests
	uv run pytest
