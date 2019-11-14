
TEST_DATA=covis-test-data/

## Docker-related tasks
TEST_TAG=amarburg/covis-worker:test
PROD_TAG=amarburg/covis-worker:prod


help:
	@echo "make build       Build test covis-worker docker image \"${TEST_TAG}\""
	@echo "make force       Build test covis-worker docker image \"${TEST_TAG}\" with --no-cache"
	@echo "make push        Push test covis-worker docker image \"${TEST_TAG}\""
	@echo "make prod        Label current test as \"prod\" and push to \"${PROD_TAG}\""


GITREV=${shell git rev-parse HEAD }
GITTAG=${shell git describe --tags }
GITDIRTY_proc=${shell git status --porcelain --untracked-files=no }
ifeq ($(.SHELLSTATUS),0)
  GITDIRTY = "False"
else
	GITDIRTY = "True"
endif


covis_worker/static_git_info.py:
	echo "def add_static_git_info( d ):\n" > $@
	printf "   d[\"covis_worker_gitrev\"] = '%s'\n" ${GITREV} >> $@
	printf "   d[\"covis_worker_gittags\"] = '%s'\n" ${GITTAG} >> $@
	printf "   d[\"covis_worker_git_dirty\"] = %s\n" ${GITDIRTY} >> $@


## Jobs related to building __test__ image
docker: covis_worker/static_git_info.py
	docker build -t ${TEST_TAG} .

force:
	docker build --no-cache -t ${TEST_TAG} .

push: build
	docker push ${TEST_TAG}

## Jobs related to building __prod__ image
prod: build
	docker tag ${TEST_TAG} ${PROD_TAG}
	docker push ${PROD_TAG}

## Run pytest
test: test_up reset_test_db
	pytest

# -V drops anonymous volumes so mongodb data isn't persisted
up:
	docker-compose -p covis up  -V

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


## Run sample jobs against local test_up network
DOCKER_NETWORK= testdata_covistest

CLIENT_ENV = -e RAW_S3_HOST=covistestdata:9000 \
							-e RAW_S3_ACCESS_KEY=covistestdata \
							-e RAW_S3_SECRET_KEY=covistestdata \
							-e OUTPUT_S3_HOST=covistestdata:9000 \
							-e OUTPUT_S3_ACCESS_KEY=covistestdata \
							-e OUTPUT_S3_SECRET_KEY=covistestdata

DOCKER_RUN=docker run --rm -it --network ${DOCKER_NETWORK} ${CLIENT_ENV}
DOCKER_RUN_TEST=${DOCKER_RUN} ${TEST_TAG}

# Attach a test worker to the covis_Default test network ... for use with non-"local"
# jobs below
test_worker: build up
	docker run --rm -it --env-file docker.env --network covis_default	${TEST_TAG}

postprocess_diffuse3.7z_local: build
	${DOCKER_RUN_TEST} covis-worker/apps/queue_postprocess.py --log DEBUG \
					--run-local s3://covis-raw/2019/10/24/COVIS-20191024T003346-diffuse3.7z \
					--output    s3://covis-postprocessed/2019/10/24/COVIS-20191024T003346-diffuse3

postprocess_diffuse3.7z_worker: build
	${DOCKER_RUN_TEST} covis-worker/apps/queue_postprocess.py  --log INFO APLUWCOVISMBSONAR001_20111001T210757.973Z-IMAGING

postprocess_local_job: build
	${DOCKER_RUN_TEST} covis-worker/apps/queue_postprocess.py --log DEBUG --job test-job --run-local APLUWCOVISMBSONAR001_20111001T210757.973Z-IMAGING

postprocess_job: build
	${DOCKER_RUN_TEST} covis-worker/apps/queue_postprocess.py --log INFO --job test-job  APLUWCOVISMBSONAR001_20111001T210757.973Z-IMAGING

## Use test docker image to import (and potentially rezip) files
## from the test SFTP site
test_sftp_import: build reset_test_db test_ssh_keys
	${DOCKER_RUN} -v $(CURDIR)/tmp/ssh_keys/:/tmp/sshkeys:ro ${TEST_TAG} \
						apps/import_sftp.py  --run-local --log INFO --privkey /tmp/sshkeys/id_rsa --force sftp://sftp:22/

test_rezip_local: build reset_test_db
	${DOCKER_RUN} -v $(CURDIR)/tmp/ssh_keys/:/tmp/sshkeys:ro ${TEST_TAG} \
					 apps/queue_rezip.py  --run-local --log INFO --skip-dmas

test_validate_db: build
	${DOCKER_RUN_TEST} apps/validate_db.py --log INFO --dry-run

test_validate_minio: build
	${DOCKER_RUN_TEST} apps/validate_minio.py --log INFO --dry-run covis-nas



## How to scrape db
## apps/run_metadata_report.py   --dbhost "mongodb://user:passwd@hostname:27017/covisprod?authSource=covisprod" | tee ${FILENAME}.csv
##




## Generate SSH keys for test SFTP server in Docker-Compose and pytest
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

.PHONY: test test_up drop_test_db reset_test_db


#---- Targets designed to be run _INSIDE THE DOCKER CONTAINER_ ----

## Use the ENV variable preferentially, otherwise here's a default
CELERY_BROKER ?= amqp://user:bitnami@localhost

flower:
	celery flower -A covis_worker --broker=${CELERY_BROKER}

worker:
	celery -A covis_worker worker -l info --concurrency 1 --without-mingle --without-gossip --events

idle:
	while true; do sleep 3600; done

covis_import_sftp_to_nas:
	apps/import_sftp.py --run-local --log INFO sftp://covis@pi.ooirsn.uw.edu/data/COVIS

covis_import_sftp_to_s3:
	apps/sftp_to_wasabi.py --bucket covis-raw --log INFO ftp://covis@pi.ooirsn.uw.edu/data/COVIS
	apps/sftp_to_wasabi.py --bucket covis-eng --log INFO ftp://covis@pi.ooirsn.uw.edu/data/COVIS-ENG





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


.PHONY: impart_dmas import_covis_nas import_seed_data  covis_worker/static_git_info.py


# Dump mongodb to a JSON test file
dump_json:
	apps/dump_mongo.py > dump.json

dump:
	apps/dump_mongo.py

backup:
	mongodump -o mongodb.backup --gzip

restore:
	mongorestore mongodb.backup

## Assumes ENV variable MONGODB_URL
##   Note the MONGODB_URL from Rancher will not work ... need to manually set
##   the server address to a local IP rather than the rancher service name "mongodb"
backup_prod:
	mongodump -vvvv --uri "${MONGODB_URL}" --out backup_prod --gzip

## Assumes a local mongodb is running
##   docker run -p 27017:27017 bitnami/mongodb:3.6
bootstrap_local:
	mongorestore -v --gzip --drop backup_prod



.PHONY:  help backup restore dump \
			import_test get_test_data build drone build push \
			docker_process_test
