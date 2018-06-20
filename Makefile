
DMAS_TOKEN=a06ed13f-8aab-4cca-9dd5-b329dde1010d


## Assumes the local
## Check that test/data/{new,old}-covis-nas exist
test:
	python3 -m pytest test/

TEST_DATA_DAT_URL=dat://8dc8f4eb4b51d286f3ed4d825016a27ca5888e24cb4fffca019c740acf01c2e4


# Build local image
build:
	docker build -t amarburg/covis-worker:latest .
	docker build -t amarburg/covis-worker:test -f docker_test_images/test_image/Dockerfile .

drone: build
	drone exec

## The services in docker_compose.yml must exist for testing
test/data/dat.json: get_test_data

get_test_data:
	mkdir -p test/data/
	cd test/ && dat clone ${TEST_DATA_DAT_URL} data/

import_test: test/data/covis_dmas.json
	#apps/import_file_list.py --dmas --log INFO  test/data/covis_dmas.json
	#apps/import_file_list.py --covis-nas old-covis-nas1 --log INFO  test/data/old_covis_nas1.txt
	#apps/import_file_list.py --covis-nas old-covis-nas6 --log INFO  test/data/old_covis_nas6.txt

test_db: test/data/covis_dmas.json
	mongo covis --eval 'db.runs.drop()'
	apps/import_file_list.py --covis-nas old-covis-nas1 --log INFO  test/data/old_covis_nas1_small.txt
	#apps/import_file_list.py --covis-nas old-covis-nas6 --log INFO  test/data/old_covis_nas6.txt

worker:
	celery -A covis_worker worker -l info --config=c



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
import_dmas:
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2010_2012.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2013.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2014.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2015.json


COVIS_NAS = 1 3 5 6
import_covis_nas:
	$(foreach var,$(COVIS_NAS),apps/import_file_list.py --log INFO --covis-nas old-covis-nas$(var) seed_data/covis-nas$(var).txt;)

import_all: import_dmas import_covis_nas



# Dump mongodb to JSON
dump:
	apps/dump_mongo.py > dump.json

backup:
	mongodump -o mongodb.backup --gzip

restore:
	mongorestore mongodb.backup

.PHONY:  backup restore dump import_all import_covis_nas import_dmas \
				import_test test get_test_data build drone
