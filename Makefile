
DMAS_TOKEN=a06ed13f-8aab-4cca-9dd5-b329dde1010d


import_all: import_dmas import_covis_nas


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
	covis_db/import_dmas_archive_file_list.py --dmas --log INFO  seed_data/covis_dmas_2010_2012.json
	covis_db/import_dmas_archive_file_list.py --dmas --log INFO  seed_data/covis_dmas_2013.json
	covis_db/import_dmas_archive_file_list.py --dmas --log INFO  seed_data/covis_dmas_2014.json
	covis_db/import_dmas_archive_file_list.py --dmas --log INFO  seed_data/covis_dmas_2015.json


COVIS_NAS = 1 3 5 6
import_covis_nas:
	$(foreach var,$(COVIS_NAS),covis_db/import_dmas_archive_file_list.py --log INFO --covis-nas covis-nas$(var) seed_data/covis-nas$(var).txt;)

dump:
	covis_db/dump_mongo.py


backup:
	mongodump -o mongodb.backup --gzip

restore:
	mongorestore mongodb.backup

PHONY:  backup restore dump import_all import_covis_nas import_dmas
