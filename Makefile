
DMAS_TOKEN=a06ed13f-8aab-4cca-9dd5-b329dde1010d



import_test:
	apps/import_file_list.py --dmas --log INFO  test/data/covis_dmas.json
	apps/import_file_list.py --covis-nas old-covis-nas1 --log INFO  test/data/old_covis_nas1.txt
	apps/import_file_list.py --covis-nas old-covis-nas6 --log INFO  test/data/old_covis_nas6.txt

## Assumes a mongoDB is running on localhost and make import_test has been run
## Check that test/data/{new,old}-covis-nas exist
test:
	python -m pytest test/





scrape_dmas:
	curl -o seed_data/covis_dmas_2010_2012.json \
					"http://dmas.uvic.ca/api/archivefiles?method=getList&token=$(DMAS_TOKEN)&station=KEMF&deviceCategory=COVIS&dateFrom=2010-01-01T00:00:00.000Z&dateTo=2013-01-01T00:00:00.000Z"
	curl -o seed_data/covis_dmas_2013.json \
					"http://dmas.uvic.ca/api/archivefiles?method=getList&token=$(DMAS_TOKEN)&station=KEMF&deviceCategory=COVIS&dateFrom=2013-01-01T00:00:00.000Z&dateTo=2014-01-01T00:00:00.000Z"
	curl -o seed_data/covis_dmas_2014.json \
					"http://dmas.uvic.ca/api/archivefiles?method=getList&token=$(DMAS_TOKEN)&station=KEMF&deviceCategory=COVIS&dateFrom=2014-01-01T00:00:00.000Z&dateTo=2015-01-01T00:00:00.000Z"
	curl -o seed_data/covis_dmas_2015.json \
					"http://dmas.uvic.ca/api/archivefiles?method=getList&token=$(DMAS_TOKEN)&station=KEMF&deviceCategory=COVIS&dateFrom=2015-01-01T00:00:00.000Z&dateTo=2018-01-01T00:00:00.000Z"

import_dmas:
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2010_2012.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2013.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2014.json
	apps/import_file_list.py --dmas --log INFO  seed_data/covis_dmas_2015.json


COVIS_NAS = 1 3 5 6
import_covis_nas:
	$(foreach var,$(COVIS_NAS),apps/import_file_list.py --log INFO --covis-nas old-covis-nas$(var) seed_data/covis-nas$(var).txt;)

import_all: import_dmas import_covis_nas



dump:
	apps/dump_mongo.py > dump.json

backup:
	mongodump -o mongodb.backup --gzip

restore:
	mongorestore mongodb.backup

.PHONY:  backup restore dump import_all import_covis_nas import_dmas \
				import_test test
