.PHONY: help setup test lint run clean docker

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Setup rápido (venv + deps + testes)
	./setup.sh

test: ## Executa todos os testes
	./venv/bin/python -m pytest tests/ -v

test-q: ## Executa testes (modo quiet)
	./venv/bin/python -m pytest tests/ -q --tb=line

lint: ## Verifica código com ruff
	./venv/bin/python -m ruff check .

lint-fix: ## Corrige problemas de lint
	./venv/bin/python -m ruff check --fix .

run: ## Inicia a API (dev)
	./venv/bin/uvicorn application.main:app --reload --port 8000

run-prod: ## Inicia a API (produção)
	./venv/bin/uvicorn application.main:app --host 0.0.0.0 --port 8000

clean: ## Limpa arquivos temporários
	rm -rf __pycache__ **/__pycache__ *.pyc .pytest_cache
	rm -f stitchguard.db

docker: ## Sobe com Docker Compose
	docker-compose up -d

docker-build: ## Build das imagens Docker
	docker-compose build

docker-stop: ## Para containers Docker
	docker-compose down

db-reset: ## Reseta o banco de dados
	rm -f stitchguard.db
	./venv/bin/python -c "from infra.storage import init_db; init_db()"

logs: ## Mostra logs da API
	docker-compose logs -f api
