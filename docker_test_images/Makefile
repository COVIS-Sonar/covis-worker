

all: covis_test_minio covis_test_minio_with_test_data

covis_test_minio: covis_test_minio/Dockerfile
	cd $@ && docker build -t amarburg/covis_test_minio .

covis_test_minio_with_test_data: covis_test_minio_with_test_data/Dockerfile
	cd $@ && docker build -t amarburg/covis_test_minio:test_data .

push: covis_test_minio covis_test_minio_with_test_data
	docker push amarburg/covis_test_minio
	docker push amarburg/covis_test_minio:test_data

clean:
	docker rmi -f covis-worker/minio_base

.PHONY: all
