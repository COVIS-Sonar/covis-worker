help:
	@echo "make download 			Downloads all of the COVIS test data.  Requires wget"

TEST_FILES = covis-raw/2019/10/24/COVIS-20191024T003346-diffuse3.tar.gz \
							covis-raw/2019/10/24/COVIS-20191024T000002-imaging1.tar.gz \
							covis-raw/2019/10/24/COVIS-20191024T003346-diffuse3.7z \
							covis-raw/2019/10/24/COVIS-20191024T000002-imaging1.7z


download: $(TEST_FILES)

%.tar.gz:
	mkdir -p $(dir $@)
	cd $(dir $@) && wget https://covis-raw.s3.wasabisys.com/$@

## Since the 7z files aren't available on the public internet,
## make them locally instead.
## Computationally expensive
%.7z: %.tar.gz
	mkdir -p $(dir $@)
	$(eval TMP := $(shell mktemp -d))
	cd $(TMP) && tar xzvf $(abspath $^) | xargs 7z a $(abspath $@)
	rm -rf $(TMP)


.phony:  help download
