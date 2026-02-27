.PHONY: help up down logs test test-unit test-integration test-e2e clean db-seed restart ps

help:
	@echo "=== P&A System - Docker Infrastructure ==="
	@echo ""
	@echo "Available commands:"
	@echo "  make up              - Start all services (MySQL + Temporal + Worker)"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - View logs from all services"
	@echo "  make ps              - Show running containers"
	@echo ""
	@echo "  make test            - Run ALL tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-e2e        - Run end-to-end tests only"
	@echo ""
	@echo "  make db-seed         - Load seed data"
	@echo "  make clean           - Stop services and remove volumes"
	@echo ""



up:
	@echo "Starting P&A stack with Docker..."
	docker compose up -d
	@echo ""
	@echo "Waiting for services to be ready..."
	@timeout /t 15 /nobreak > nul
	@echo ""
	@echo "✅ Stack is running!"
	@echo ""
	@echo "Services available:"
	@echo "  - MySQL:       localhost:3306"
	@echo "  - Temporal:    localhost:7233"
	@echo "  - Temporal UI: http://localhost:8080"
	@echo ""

down:
	@echo "Stopping all services..."
	docker compose down
	@echo "✅ All services stopped"

restart:
	@echo "Restarting all services..."
	docker compose restart
	@echo "✅ Services restarted"

logs:
	docker compose logs -f

ps:
	docker compose ps

test: up
	@echo "Running ALL tests..."
	docker compose exec worker pytest -v tests/
	@echo "✅ Tests completed"

test-unit:
	@echo "Running unit tests..."
	docker compose exec worker pytest -v tests/unit/
	@echo "✅ Unit tests completed"

test-integration: up
	@echo "Running integration tests..."
	docker compose exec worker pytest -v tests/integration/
	@echo "✅ Integration tests completed"

test-e2e: up
	@echo "Running end-to-end tests..."
	docker compose exec worker pytest -v -m e2e tests/e2e/
	@echo "✅ E2E tests completed"

db-seed: up
	@echo "Loading seed data..."
	docker compose exec -T mysql mysql -u$${MYSQL_USER} -p$${MYSQL_PASSWORD} $${MYSQL_DATABASE} < db/seeds/010_seed_master_data.sql
	docker compose exec -T mysql mysql -u$${MYSQL_USER} -p$${MYSQL_PASSWORD} $${MYSQL_DATABASE} < db/seeds/020_seed_test_data.sql
	docker compose exec -T mysql mysql -u$${MYSQL_USER} -p$${MYSQL_PASSWORD} $${MYSQL_DATABASE} < db/seeds/030_seed_validations.sql
	@echo "✅ Seed data loaded"

clean:
	@echo "Stopping services and cleaning volumes..."
	docker compose down -v
	@echo "✅ Cleanup complete"
