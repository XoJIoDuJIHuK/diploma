build_base_local:
	docker build -t diploma-base -f ./contrib/docker/base/Dockerfile .

build_local: build_base_local
	docker compose --env-file=.local.env -f contrib/docker/docker-compose.local.yml build

up:
	docker compose --env-file=.local.env -f contrib/docker/docker-compose.local.yml -p diploma up -d

up_build:
	docker compose --env-file=.local.env -f contrib/docker/docker-compose.local.yml -p diploma up -d --build

build_up_local: build_local up_local

down:
	docker compose --env-file=.local.env -f contrib/docker/docker-compose.local.yml -p diploma down --remove-orphans

pack_tarball:
	tar -czvf diploma.tar.gz --exclude-from=.gitignore .

up_g4f:
	docker compose 
