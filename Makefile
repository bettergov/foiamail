PROJNAME=foiamail

deploy:
	rsync -avC --exclude='*.pyc' --exclude='report/reports/response.csv' \
		--progress --delete \
		./ $${DEPLOY_USER}@$${DEPLOY_HOST}:$${DEPLOY_DIR}

docker_build:
	@echo "Building ${PROJNAME} docker image"
	docker build . -t ${PROJNAME}
	docker volume create ${PROJNAME}_logs

docker_start:
	@echo "Starting ${PROJNAME}"
	docker run \
		--mount source=${PROJNAME}_logs,target=/home/ubuntu/foiamail/log/logs \
		-d -t ${PROJNAME}

docker_stop:
	@echo "Stopping ${PROJNAME}"
	docker stop $$(docker ps | grep ${PROJNAME} | awk '{print $$1}')

docker_attach:
	docker exec -t -i  $$(docker ps | grep foiamail | head -n 1 | awk '{print $$1}')  /bin/bash

docker_rebuild: docker_stop docker_build docker_start
