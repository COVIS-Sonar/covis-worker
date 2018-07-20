

Contains the following Python packages:

 - `covis_db` is a Python library that encapsulates a Mongo DB instance which stores
 information about COVIS data files.

 - `covis_worker` is a Python library which instantiates a Celery worker



# MongoDB Schema

A non-authoritative DB of COVIS runs is stored in MongoDB.   A thin Python wrapper is
provided by the `covis_db/` package in this repo.   The default database is `covis`.

The `runs` table stores one entry per "run" (sonar data collection) by COVIS.   A sample record is

    {'_id': ObjectId('5b2987614af0aa9aa7128e95'),
     'basename': 'APLUWCOVISMBSONAR001_20141219T154622.072Z-DIFFUSE',
     'datetime': datetime.datetime(2014, 12, 19, 15, 46, 22, 72000),
     'mode': 'DIFFUSE',
     'raw': [{'filename': '2014/12/19/APLUWCOVISMBSONAR001_20141219T154622.072Z-DIFFUSE.tar.gz',
              'host': 'OLD-COVIS-NAS6'}],
     'site': 'Endeavour'}

By default records are indexed by `basename` which is a unique text identifier for the run.   At
ONC, this name is derived from start date/time and mode of the run, but in general the basename _shouldn't_ be parsed to extract selection information.  Instead, the date/time, mode, and site are broken out into separate fields which can be used to select within the db.

The `raw` field contains an array of raw file locations.   `filename` and `host` should be sufficient information to determine a method of access of the raw file -- whether local file access, S3, etc.
