

all: covis_test_minio

covis_test_minio: covis_test_minio/Dockerfile
	cd $@ && docker build -t covis-worker/$@ .

# minio_old_nas: minio_base
# 	cd $@ && docker build -t amarburg/covis_test_$@ .
#
# minio_new_nas: minio_base
# 	cd $@ && docker build -t amarburg/covis_test_$@ .
#
# push:
# 	docker push amarburg/covis_test_minio_old_nas
# 	docker push amarburg/covis_test_minio_new_nas

clean:
	docker rmi -f covis-worker/minio_base #amarburg/covis_test_minio_old_nas amarburg/covis_test_minio_new_nas

.PHONY: all
