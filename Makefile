#!make
include .env
export


install:
	docker-compose up -d

create.db:
	docker-compose exec ylab_app alembic upgrade head

backend.run:
	docker-compose exec ylab_app python ./main.py

down:
	docker-compose down

backend.logs:
	docker-compose logs ylab_app

db.logs:
	docker-compose logs --tail="all" -f ylab_postgres_db

backend.config:
	docker-compose exec -m src.core

backend.build:
	docker-compose up -d --no-deps --build ylab_app