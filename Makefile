include .env.common
-include .env.local
export

DOCKER_USER = osferna
IMAGE = $(DOCKER_USER)/ai-email-assistant

COMPOSE_FILES = -f docker-compose.yml -f docker-compose-dev.yml

## Gmail OAuth
## Genera token.json a partir de credentials.json (requiere navegador).
## Uso: make gmail-token
gmail-token:
	python3 -m venv .venv-oauth && .venv-oauth/bin/pip install -q google-auth-oauthlib && .venv-oauth/bin/python generate_token.py

build:
	docker build --build-arg PYTHON_VERSION=$(PYTHON_VERSION) -t $(IMAGE):latest ./django
	docker push $(IMAGE):latest

up:
	docker compose $(COMPOSE_FILES) up --build -d

down:
	docker compose $(COMPOSE_FILES) down

downup: down up

makemigrations:
	docker compose $(COMPOSE_FILES) exec web python manage.py makemigrations

migrate:
	docker compose $(COMPOSE_FILES) exec web python manage.py migrate

test:
	docker compose $(COMPOSE_FILES) exec web python manage.py test

logs:
	docker compose $(COMPOSE_FILES) logs -f

shell:
	docker compose $(COMPOSE_FILES) exec web sh

django-shell:
	docker compose $(COMPOSE_FILES) exec web python manage.py shell
