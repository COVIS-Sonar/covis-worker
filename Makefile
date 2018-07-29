


TEST_DATA=covis-test-data/

## Docker-related tasks

TAG=amarburg/covis-worker:latest

build:
	docker build -t ${TAG} .

force:
	docker build --no-cache -t ${TAG} .


push: build
	docker push ${TAG}

process_local: build
	docker run --rm -it --env-file docker.env --network covis_default --entrypoint python3 ${TAG} apps/queue_postprocess.py  --log DEBUG --run-local APLUWCOVISMBSONAR001_20111001T210757.973Z-IMAGING

process_local_job: build
	docker run --rm -it --env-file docker.env --network covis_default --entrypoint python3 ${TAG} apps/queue_postprocess.py  --log DEBUG --job test-job --run-local APLUWCOVISMBSONAR001_20111001T210757.973Z-IMAGING

process: build
	docker run --rm -it --env-file docker.env --network covis_default --entrypoint python3 ${TAG} apps/queue_postprocess.py  --log INFO APLUWCOVISMBSONAR001_20111001T210757.973Z-IMAGING

process_job: build
	docker run --rm -it --env-file docker.env --network covis_default --entrypoint python3 ${TAG} apps/queue_postprocess.py  --log INFO --job test-job  APLUWCOVISMBSONAR001_20111001T210757.973Z-IMAGING


sftp_test: build
		docker run --rm -it --env-file docker.env -e SFTP_PRIVKEY_FILE=/tmp/sshkeys/id_rsa -v $(CURDIR)/tmp/ssh_keys/:/tmp/sshkeys:ro --network covis-worker_default --entrypoint python3 ${TAG} apps/import_sftp.py  --run-local --log INFO --force sftp://sftp:22/



## Check that test/data/{new,old}-covis-nas exist
test:
	pytest

## Temporary SSH keys for test SFTP server in Docker-Compose and pytest
test_ssh_keys: tmp/ssh_keys/id_rsa.pub

tmp/ssh_keys/id_rsa.pub:
	mkdir -p tmp/ssh_keys/
	ssh-keygen -t ed25519 -f tmp/ssh_keys/ssh_host_ed25519_key < /dev/null
	ssh-keygen -t rsa -b 4096 -f tmp/ssh_keys/ssh_host_rsa_key < /dev/null
	ssh-keygen -t rsa -b 4096 -f tmp/ssh_keys/id_rsa < /dev/null

## Sftp into the sftp test server created by docker-compose.yml
sftp:
	sftp -P 2222 -i tmp/ssh_keys/id_rsa covis@localhost

.PHONY: test_ssh_keys





# Build local image
# test_build:
# 	docker build -t amarburg/covis-worker:test -f docker_test_images/test_image/Dockerfile .

drone: build
	drone exec

## The services in docker_compose.yml must exist for testing
drop_test_db:
	mongo covis --eval 'db.runs.drop()'

## Builds the small db
${TEST_DATA}/test_db.bson: ${TEST_DATA}/old_covis_nas1.txt ${TEST_DATA}/covis_dmas.json
	mongo covis --eval 'db.runs.drop()'
	apps/import_file_list.py --covis-nas old-covis-nas1 --log INFO ${TEST_DATA}/old_covis_nas1.txt
	apps/import_file_list.py --dmas --log INFO ${TEST_DATA}/covis_dmas.json
	mongodump -d covis -c runs -o - > $@

reset_test_db: ${TEST_DATA}/test_db.bson
	mongorestore -d covis -c runs --drop --dir=- < $<



## Builds the large db
# bootstrap_large_db: test/data/covis_dmas.json
# 	mongo covis --eval 'db.runs.drop()'
# 	apps/import_file_list.py --dmas --log INFO  test/data/covis_dmas.json
# 	apps/import_file_list.py --covis-nas old-covis-nas1 --log INFO  test/data/old_covis_nas1.txt
# 	apps/import_file_list.py --covis-nas old-covis-nas6 --log INFO  test/data/old_covis_nas6.txt
# 	mongodump -d covis -c runs -o - > test/data/large_db_dump.bson
#
# reset_large_db: test/data/large_db_dump.bson
# 	mongorestore -d covis -c runs --drop --dir=- < $^


.PHONY: drop_test_db reset_test_db



## Targets that relate to running the worker

docker_worker: build
	docker run --rm -it --env-file docker.env --network covis_default	${TAG}

worker:
	celery -A covis_worker worker -l info --concurrency 1 --without-mingle --without-gossip --events

## Use the ENV variable preferentially, otherwise here's a default
CELERY_BROKER ?= amqp://user:bitnami@localhost

flower:
	celery flower -A covis_worker --broker=${CELERY_BROKER}




#  Retrieve list of 2010-2015 COVIS files currently on ONC DMAS
#  Saves results to seed_data/
scrape_dmas:
	curl -o seed_data/covis_dmas_2010_2012.json \
					"http://dmas.uvic.ca/api/archivefiles?method=getList&token=$(DMAS_TOKEN)&station=KEMF&deviceCategory=COVIS&dateFrom=2010-01-01T00:00:00.000Z&dateTo=2013-01-01T00:00:00.000Z"
	curl -o seed_data/covis_dmas_2013.json \
					"http://dmas.uvic.ca/api/archivefiles?method=getList&token=$(DMAS_TOKEN)&station=KEMF&deviceCategory=COVIS&dateFrom=2013-01-01T00:00:00.000Z&dateTo=2014-01-01T00:00:00.000Z"
	curl -o seed_data/covis_dmas_2014.json \
					"http://dmas.uvic.ca/api/archivefiles?method=getList&token=$(DMAS_TOKEN)&station=KEMF&deviceCategory=COVIS&dateFrom=2014-01-01T00:00:00.000Z&dateTo=2015-01-01T00:00:00.000Z"
	curl -o seed_data/covis_dmas_2015.json \
					"http://dmas.uvic.ca/api/archivefiles?method=getList&token=$(DMAS_TOKEN)&station=KEMF&deviceCategory=COVIS&dateFrom=2015-01-01T00:00:00.000Z&dateTo=2018-01-01T00:00:00.000Z"

#  Import DMAS and local NAS seed_data to a MongoDB instance
import_dmas: seed_data/covis_dmas_*.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2010_2012.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2013.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2014.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2015.json


COVIS_NAS = 1 3 5 6
import_covis_nas: seed_data/covis-nas?.txt
	$(foreach var,$(COVIS_NAS),apps/import_file_list.py --log INFO --covis-nas old-covis-nas$(var) seed_data/covis-nas$(var).txt;)

seed_data/seed_data.bson: drop_db import_dmas import_covis_nas
	mongodump -d covis -o - > seed_data/seed_data.bson

import_seed_data: seed_data.bson
		mongorestore -d covis -c runs --drop --dir=- < seed_data/seed_data.bson


.PHONY: impart_dmas import_covis_nas import_seed_data


# Dump mongodb to JSON
dump:
	apps/dump_mongo.py > dump.json

backup:
	mongodump -o mongodb.backup --gzip

restore:
	mongorestore mongodb.backup

.PHONY:  backup restore dump \
			import_test test get_test_data build drone build push \
			docker_process_test
