include .env.common
-include .env.local
export

COMPOSE_FILES = -f docker-compose.yml -f docker-compose-dev.yml

up:
	docker compose $(COMPOSE_FILES) up --build -d

down:
	docker compose $(COMPOSE_FILES) down

migrate:
	docker compose $(COMPOSE_FILES) exec web python manage.py migrate

test:
	docker compose $(COMPOSE_FILES) exec web python manage.py test

logs:
	docker compose $(COMPOSE_FILES) logs -f

shell:
	docker compose $(COMPOSE_FILES) exec web python manage.py shell
