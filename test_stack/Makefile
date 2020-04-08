help:
	@echo "make download 			Downloads all of the COVIS test data.  Requires wget"

TGZ_DIR = sftp-host
T7Z_DIR = covis-nas/covis-raw

TEST_FILES = 2019/10/24/COVIS-20191024T003346-diffuse3.tar.gz \
							2019/10/24/COVIS-20191024T000002-imaging1.tar.gz \
							2019/10/24/COVIS-20191024T003346-diffuse3.7z \
							2019/10/24/COVIS-20191024T000002-imaging1.7z

download: $(TEST_FILES)

%.tar.gz:
	mkdir -p ${TGZ_DIR}/$(dir $@)
	cd ${TGZ_DIR}/$(dir $@) && wget https://covis-raw.s3.wasabisys.com/$@


## Since the 7z files aren't available on the public internet,
## make them locally instead.
## Computationally expensive
%.7z: %.tar.gz
	mkdir -p ${T7Z_DIR}/$(dir $@)
	$(eval TMP := $(shell mktemp -d))
	cd $(TMP) && tar xzvf $(abspath ${T7Z_DIR}/$^) | xargs 7z a $(abspath ${T7Z_DIR}/$@)
	rm -rf $(TMP)


.phony:  help download
