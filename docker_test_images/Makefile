

all: minio_old_nas minio_new_nas

minio_base:
	cd $@ && docker build -t covis-worker/$@ .

minio_old_nas: minio_base
	cd $@ && docker build -t covis-worker/$@ .

minio_new_nas: minio_base
	cd $@ && docker build -t covis-worker/$@ .

clean:
	docker rmi -f covis-worker/minio_base covis-worker/minio_old_nas covis-worker/minio_new_nas

.PHONY: all minio_old_nas minio_new_nas minio_base
