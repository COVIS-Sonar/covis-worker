# COVIS-Worker

This repository contains tools used to run the Matlab-based analysis tools in the [covis-postprocessing](https://github.com/COVIS-Sonar/postprocessing) repository at scale in a Docker cluster.

__High-level documentation of the post-processing suite is stored in the [`Docs/`](https://github.com/COVIS-Sonar/postprocessing/tree/master/Docs) directory in the [covis-postprocessing](https://github.com/COVIS-Sonar/postprocessing) repository.__

This repo get packaged into the [`amarburg/covis-worker`]() Docker image, which
does all of the work, supported by other "stock" Docker images.  A minimal
COVIS-worker deployment includes instances of:

  * [rabbitmq](https://www.rabbitmq.com/).   covis-worker jobs are managed
  by [celery](http://www.celeryproject.org) using a
  [rabbitmq broker](https://www.rabbitmq.com).

  * [MongoDB](https://www.mongodb.com/).   COVIS data files are catalogued in
  a MongoDB instance.   This database is __non-authoritative__  --- the truth
  is what's stored on disk, the d/b is just a convenient index of those
  contents.  It can be rebuilt at any time by comparison with disk.

  * [Minio](https://www.minio.io).   All file I/O is handled through an
  S3-ish interface provided by one or more instances if
  [minio](https://www.minio.io)

A sample cluster can be found in the `docker-compose.yml` file in this
repo, which is used for testing.


# The covis-worker

The covis-worker itself consists of two Python packages and a small set of
command-line scripts in the `apps/` directory.     Many of the
post-processing tasks use compiled Matlab code from the
[covis-postprocessing](ttps://github.com/COVIS-Sonar/postprocessing)
package, typically compiled into a Docker image, which the `Dockerfile`
in this repo uses as a base image.

The `covis_db` library interacts with the MongoDB database.

`covis_worker` contains the worker functions for the Celery app.



# MongoDB Schema

A non-authoritative DB of COVIS runs is stored in MongoDB.   A thin Python
wrapper is provided by the `covis_db/` package in this repo.   The default
database is `covis`.

The `runs` table stores one entry per "run" (sonar data collection) by COVIS.
A sample record is

    {'_id': ObjectId('5b2987614af0aa9aa7128e95'),
     'basename': 'APLUWCOVISMBSONAR001_20141219T154622.072Z-DIFFUSE',
     'datetime': datetime.datetime(2014, 12, 19, 15, 46, 22, 72000),
     'mode': 'DIFFUSE',
     'raw': [{'filename': '2014/12/19/APLUWCOVISMBSONAR001_20141219T154622.072Z-DIFFUSE.tar.gz',
              'host': 'OLD-COVIS-NAS6'}],
     'site': 'Endeavour'
   }

By default records are indexed by `basename` which is a unique text
identifier for the run.   At ONC, this name is derived from start date/time
and mode of the run, but in general the basename _shouldn't_ be parsed to
extract selection information.  Instead, the date/time, mode, and site are
broken out into separate fields which can be used to select within the db.

The `raw` field contains an array of raw file locations.   `filename` and
`host` should be sufficient information to determine a method of access of
the raw file -- whether local file access, S3, etc.
