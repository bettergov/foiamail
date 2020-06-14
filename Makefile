PROJNAME=foiamail

deploy:
	rsync -avC --exclude='*.pyc'  --progress --delete \
		./ $${DEPLOY_USER}@$${DEPLOY_HOST}:$${DEPLOY_DIR}

docker_build:
	docker build . -t ${PROJNAME}
	docker volume create ${PROJNAME}_logs

docker_start:
	docker run \
		--mount source=${PROJNAME}_logs,target=/home/ubuntu/foiamail/log/logs \
		-d -t ${PROJNAME}

docker_stop:
	docker stop $$(docker ps | grep ${PROJNAME} | awk '{print $$1}')

docker_attach:
	docker exec -t -i  $$(docker ps | grep foiamail | head -n 1 | awk '{print $$1}')  /bin/bash
